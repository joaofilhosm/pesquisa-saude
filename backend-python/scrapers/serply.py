"""
Scraper do Google Scholar via Serply.io

Serply é uma API para Google Search e Google Scholar.
Documentação: https://serply.io/docs

Variável de ambiente:
  SERPLY_API_KEY — chave da API (https://serply.io)
"""
import httpx
import os
from typing import List, Dict, Any, Optional

from .cache import cache_medio


class SerplyScraper:
    """
    Scraper para Google Scholar via Serply.io.

    API confiável para Google Scholar sem bloqueios.
    """

    API_URL = "https://api.serply.io/v1/scholar"

    def __init__(self):
        self.api_key = os.getenv("SERPLY_API_KEY")
        self.timeout = int(os.getenv("HTTP_TIMEOUT", "30"))

    async def buscar(self, termo: str, ano_min: int = 2016) -> List[Dict[str, Any]]:
        """
        Busca artigos no Google Scholar via Serply.io.

        Retorna lista vazia se a API key não estiver configurada ou a busca falhar.
        """
        if not self.api_key:
            return []

        cache_key = f"serply_{termo}_{ano_min}"
        cached = cache_medio.get(cache_key)
        if cached is not None:
            return cached

        resultados: List[Dict[str, Any]] = []
        try:
            headers = {
                "X-API-Key": self.api_key,
                "Accept": "application/json",
                "User-Agent": "PesquisaSaude/3.0 (https://github.com/joaofilhosm/pesquisa-saude)",
            }
            params = {
                "q": termo,
                "num": 20,
            }

            async with httpx.AsyncClient(headers=headers, timeout=self.timeout) as client:
                response = await client.get(self.API_URL, params=params)
                if response.status_code == 200:
                    resultados = self._parse_resultados(response.json(), termo, ano_min)
                elif response.status_code == 401:
                    print("Serply.io: chave inválida ou ausente.")
                elif response.status_code == 429:
                    print("Serply.io: limite de requisições atingido.")
                else:
                    print(f"Serply.io: status {response.status_code}")

        except Exception as e:
            print(f"Erro Serply.io: {e}")

        cache_medio.set(cache_key, resultados)
        return resultados

    def _parse_resultados(self, data: Dict, termo: str, ano_min: int) -> List[Dict[str, Any]]:
        """Converte resposta JSON da Serply.io para o formato padrão."""
        resultados = []
        papers = data.get("scholar", []) if isinstance(data, dict) else []

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
                resumo: Optional[str] = (paper.get("summary") or paper.get("snippet") or "").strip() or None
                if resumo and len(resumo) > 3000:
                    resumo = resumo[:3000]

                # URL
                url: Optional[str] = paper.get("link")

                # DOI
                doi: Optional[str] = paper.get("doi")

                # PMID
                pmid: Optional[str] = None
                if "pubmed" in (url or "").lower():
                    pmid = url.split("pubmed")[-1].split("/")[0].lstrip("/") if "pubmed" in url else None

                # Journal
                journal: Optional[str] = paper.get("publication")

                # Citações
                citation_count: Optional[int] = None
                cites = paper.get("cited_by")
                if cites:
                    citation_count = int(cites) if str(cites).isdigit() else None

                resultados.append({
                    "id": None,
                    "titulo": titulo,
                    "autores": autores,
                    "resumo": resumo,
                    "url": url,
                    "fonte": "Google Scholar (Serply.io)",
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
