"""
Scraper do Google Scholar via SerpAPI

SerpAPI é uma API paga que fornece acesso ao Google Scholar sem bloqueios.
Documentação: https://serpapi.com/google-scholar-api

Variável de ambiente:
  SERPAPI_KEY — chave da API (https://serpapi.com/manage-api-key)
"""
import httpx
import os
from typing import List, Dict, Any, Optional

from .cache import cache_medio


class SerpAPIScraper:
    """
    Scraper para Google Scholar via SerpAPI.

    Alternativa robusta ao scraping direto: API paga, confiável,
    sem risco de bloqueio por CAPTCHA.
    """

    API_URL = "https://serpapi.com/search"

    def __init__(self):
        self.api_key = os.getenv("SERPAPI_KEY")
        self.timeout = int(os.getenv("HTTP_TIMEOUT", "30"))

    async def buscar(self, termo: str, ano_min: int = 2016) -> List[Dict[str, Any]]:
        """
        Busca artigos no Google Scholar via SerpAPI.

        Retorna lista vazia se a API key não estiver configurada ou a busca falhar.
        """
        if not self.api_key:
            return []

        cache_key = f"serpapi_{termo}_{ano_min}"
        cached = cache_medio.get(cache_key)
        if cached is not None:
            return cached

        resultados: List[Dict[str, Any]] = []
        try:
            params = {
                "engine": "google_scholar",
                "q": termo,
                "api_key": self.api_key,
                "num": 20,
            }

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(self.API_URL, params=params)
                if response.status_code == 200:
                    resultados = self._parse_resultados(response.json(), termo, ano_min)
                elif response.status_code == 401:
                    print("SerpAPI: chave inválida ou ausente.")
                elif response.status_code == 429:
                    print("SerpAPI: limite de requisições atingido.")
                else:
                    print(f"SerpAPI: status {response.status_code}")

        except Exception as e:
            print(f"Erro SerpAPI: {e}")

        cache_medio.set(cache_key, resultados)
        return resultados

    def _parse_resultados(self, data: Dict, termo: str, ano_min: int) -> List[Dict[str, Any]]:
        """Converte resposta JSON da SerpAPI para o formato padrão."""
        resultados = []
        papers = data.get("organic_results", [])

        for paper in papers:
            try:
                titulo = (paper.get("title") or "").strip()
                if not titulo or len(titulo) < 5:
                    continue

                # Ano
                ano: Optional[int] = None
                year_str = paper.get("year")
                if year_str:
                    try:
                        ano = int(str(year_str))
                        if ano < ano_min:
                            continue
                    except (ValueError, TypeError):
                        pass

                # Autores
                autores: Optional[List[str]] = None
                authors_raw = paper.get("authors") or []
                if authors_raw:
                    autores = [a.get("name", "").strip() for a in authors_raw if a.get("name")][:10]

                # Resumo
                resumo: Optional[str] = (paper.get("snippet") or "").strip() or None
                if resumo and len(resumo) > 3000:
                    resumo = resumo[:3000]

                # URL
                url: Optional[str] = paper.get("link") or paper.get("url")

                # DOI
                doi: Optional[str] = paper.get("doi")
                if not doi:
                    link = url or ""
                    if "doi.org" in link:
                        doi = link.split("doi.org/")[-1].split("/")[0] if "doi.org/" in link else None

                # PMID
                pmid: Optional[str] = None
                if "pubmed" in (url or "").lower():
                    pmid = url.split("pubmed")[-1].split("/")[0].lstrip("/") if "pubmed" in url else None

                # Journal
                journal: Optional[str] = paper.get("publication")

                # Citações
                citation_count: Optional[int] = None
                citations = paper.get("inline_links", {}).get("cited_by")
                if citations:
                    citation_count = citations.get("total", 0)

                resultados.append({
                    "id": None,
                    "titulo": titulo,
                    "autores": autores,
                    "resumo": resumo,
                    "url": url,
                    "fonte": "Google Scholar (SerpAPI)",
                    "journal": journal,
                    "volume": "",
                    "issue": "",
                    "paginas": "",
                    "tipo": "artigo",
                    "ano": ano,
                    "doi": doi,
                    "pmid": pmid,
                    "citation_count": citation_count,
                    "keywords": [termo],
                })
            except Exception:
                continue

        return resultados
