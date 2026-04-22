"""
Scraper do Semantic Scholar - Substituto prático do Google Acadêmico

Usa a Graph API oficial do Semantic Scholar (Allen Institute for AI),
gratuita e sem risco de bloqueio. Cobre mais de 200 milhões de papers
acadêmicos, incluindo toda a produção em ciências da saúde.

Referência: https://api.semanticscholar.org/api-docs/graph#tag/Paper-Data/operation/get_graph_paper_bulk_search

Variável de ambiente opcional:
  S2_API_KEY — gratuita em https://www.semanticscholar.org/product/api
  Sem chave: ~1 req/s · Com chave: ~10 req/s e acesso a campos extras
"""
import httpx
import os
import re
from typing import List, Dict, Any, Optional

from .cache import cache_medio


class SemanticScholarScraper:
    """
    Scraper para Semantic Scholar via Graph API oficial.

    Alternativa robusta ao Google Acadêmico: API pública, gratuita,
    sem risco de bloqueio por CAPTCHAs, com mais de 200 M de papers.
    Inclui campo citationCount ausente nas demais fontes.

    Configure S2_API_KEY no .env para aumentar o rate limit (opcional).
    """

    API_URL = "https://api.semanticscholar.org/graph/v1/paper/search"
    FIELDS = (
        "title,authors,year,externalIds,abstract,url,"
        "citationCount,publicationVenue,journal"
    )

    def __init__(self):
        self.api_key = os.getenv("S2_API_KEY")
        self.headers: Dict[str, str] = {
            "User-Agent": "PesquisaSaude/3.0 (https://github.com/joaofilhosm/pesquisa-saude)",
            "Accept": "application/json",
        }
        if self.api_key:
            self.headers["x-api-key"] = self.api_key

    async def buscar(self, termo: str, ano_min: int = 2016) -> List[Dict[str, Any]]:
        """
        Busca artigos no Semantic Scholar via Graph API.

        Retorna lista vazia se a busca falhar (sem dados fictícios).
        """
        cache_key = f"semanticscholar_{termo}_{ano_min}"
        cached = cache_medio.get(cache_key)
        if cached is not None:
            return cached

        resultados: List[Dict[str, Any]] = []
        try:
            params = {
                "query": termo,
                "fields": self.FIELDS,
                "limit": 20,
                "year": f"{ano_min}-",
            }

            async with httpx.AsyncClient(headers=self.headers, timeout=30) as client:
                response = await client.get(self.API_URL, params=params)
                if response.status_code == 200:
                    resultados = self._parse_resultados(response.json(), termo)
                elif response.status_code == 429:
                    print("Semantic Scholar: rate limit atingido. Configure S2_API_KEY para aumentar o limite.")
                elif response.status_code == 401:
                    print("Semantic Scholar: S2_API_KEY inválida.")
                else:
                    print(f"Semantic Scholar: status {response.status_code}")

        except Exception as e:
            print(f"Erro Semantic Scholar: {e}")

        cache_medio.set(cache_key, resultados)
        return resultados

    def _parse_resultados(self, data: Dict, termo: str) -> List[Dict[str, Any]]:
        """Converte resposta JSON da Semantic Scholar API para o formato padrão."""
        resultados = []
        papers = data.get("data", [])

        for paper in papers:
            try:
                titulo = (paper.get("title") or "").strip()
                if not titulo or len(titulo) < 5:
                    continue

                # Autores
                autores: Optional[List[str]] = None
                autores_raw = paper.get("authors") or []
                if autores_raw:
                    autores = [
                        a.get("name", "").strip()
                        for a in autores_raw
                        if a.get("name")
                    ][:10]

                # Ano
                ano: Optional[int] = paper.get("year")

                # Filtrar anos fora do intervalo (API pode não filtrar com precisão)
                if ano and ano < 2000:
                    continue

                # DOI e PMID via externalIds
                ext = paper.get("externalIds") or {}
                doi: Optional[str] = ext.get("DOI")
                pmid: Optional[str] = str(ext.get("PubMed")) if ext.get("PubMed") else None

                # URL
                url: Optional[str] = paper.get("url")
                if not url and doi:
                    url = f"https://doi.org/{doi}"
                if not url:
                    paper_id = paper.get("paperId")
                    if paper_id:
                        url = f"https://www.semanticscholar.org/paper/{paper_id}"

                # Resumo
                resumo: Optional[str] = (paper.get("abstract") or "").strip() or None
                if resumo and len(resumo) > 3000:
                    resumo = resumo[:3000]

                # Journal / periódico
                journal: Optional[str] = None
                venue = paper.get("publicationVenue") or {}
                if venue.get("name"):
                    journal = venue["name"]
                elif paper.get("journal") and paper["journal"].get("name"):
                    journal = paper["journal"]["name"]

                # Contagem de citações (campo exclusivo desta fonte)
                citation_count: Optional[int] = paper.get("citationCount")

                resultados.append({
                    "titulo": titulo,
                    "autores": autores if autores else None,
                    "resumo": resumo,
                    "url": url,
                    "fonte": "Semantic Scholar",
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
