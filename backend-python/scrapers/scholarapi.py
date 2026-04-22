"""
Scraper do Google Scholar via ScholarAPI.net

ScholarAPI é uma API especializada em Google Scholar.
Documentação: https://scholarapi.net/docs

Variável de ambiente:
  SCHOLARAPI_KEY — chave da API (https://scholarapi.net)
"""
import httpx
import os
from typing import List, Dict, Any, Optional

from .cache import cache_medio


class ScholarAPIScraper:
    """
    Scraper para Google Scholar via ScholarAPI.net.

    API especializada em Google Scholar, confiável e sem bloqueios.
    """

    API_URL = "https://scholarapi.net/api/search"

    def __init__(self):
        self.api_key = os.getenv("SCHOLARAPI_KEY")
        self.timeout = int(os.getenv("HTTP_TIMEOUT", "30"))

    async def buscar(self, termo: str, ano_min: int = 2016) -> List[Dict[str, Any]]:
        """
        Busca artigos no Google Scholar via ScholarAPI.net.

        Retorna lista vazia se a API key não estiver configurada ou a busca falhar.
        """
        if not self.api_key:
            return []

        cache_key = f"scholarapi_{termo}_{ano_min}"
        cached = cache_medio.get(cache_key)
        if cached is not None:
            return cached

        resultados: List[Dict[str, Any]] = []
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Accept": "application/json",
            }
            params = {
                "q": termo,
                "limit": 20,
            }

            async with httpx.AsyncClient(headers=headers, timeout=self.timeout) as client:
                response = await client.get(self.API_URL, params=params)
                if response.status_code == 200:
                    data = response.json()
                    papers = data.get("data", []) if isinstance(response.json(), dict) else []
                    resultados = self._parse_resultados(papers, termo, ano_min)
                elif response.status_code == 401:
                    print("ScholarAPI.net: chave inválida ou ausente.")
                elif response.status_code == 429:
                    print("ScholarAPI.net: limite de requisições atingido.")
                else:
                    print(f"ScholarAPI.net: status {response.status_code}")

        except Exception as e:
            print(f"Erro ScholarAPI.net: {e}")

        cache_medio.set(cache_key, resultados)
        return resultados

    def _parse_resultados(self, papers: list, termo: str, ano_min: int) -> List[Dict[str, Any]]:
        """Converte resposta JSON da ScholarAPI.net para o formato padrão."""
        resultados = []

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
                resumo: Optional[str] = (paper.get("abstract") or paper.get("snippet") or "").strip() or None
                if resumo and len(resumo) > 3000:
                    resumo = resumo[:3000]

                # URL
                url: Optional[str] = paper.get("url") or paper.get("link")

                # DOI
                doi: Optional[str] = paper.get("doi")

                # PMID
                pmid: Optional[str] = None
                if "pubmed" in (url or "").lower():
                    pmid = url.split("pubmed")[-1].split("/")[0].lstrip("/") if "pubmed" in url else None

                # Journal
                journal: Optional[str] = paper.get("journal") or paper.get("venue")

                # Citações
                citation_count: Optional[int] = paper.get("citations") or paper.get("citation_count")

                resultados.append({
                    "id": None,
                    "titulo": titulo,
                    "autores": autores,
                    "resumo": resumo,
                    "url": url,
                    "fonte": "Google Scholar (ScholarAPI.net)",
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
