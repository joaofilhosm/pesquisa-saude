"""
Scraper do Google Scholar via SerpAPI

Usa a SerpAPI (https://serpapi.com) para buscar no Google Scholar
sem risco de bloqueio por CAPTCHAs ou rate limits diretos.

Requer variável de ambiente SERPAPI_KEY.
Sem a chave configurada, o scraper retorna lista vazia sem erros.

Planos:
  - Gratuito: 100 buscas/mês (suficiente para testes)
  - Pago: a partir de ~$50/mês para volumes maiores

Referência: https://serpapi.com/google-scholar-api
"""
import httpx
import os
import re
from typing import List, Dict, Any, Optional
from datetime import datetime

from .cache import cache_medio


class GoogleScholarScraper:
    """
    Scraper para Google Scholar via SerpAPI.

    Retorna lista vazia se SERPAPI_KEY não estiver configurada
    ou se a busca falhar (sem dados fictícios).

    Obtenha sua chave gratuita (100 buscas/mês) em:
    https://serpapi.com/manage-api-key
    """

    SERPAPI_URL = "https://serpapi.com/search"

    def __init__(self):
        self.api_key = os.getenv("SERPAPI_KEY")
        self.headers = {
            "User-Agent": "PesquisaSaude/3.0 (https://github.com/joaofilhosm/pesquisa-saude)",
            "Accept": "application/json",
        }

    async def buscar(self, termo: str, ano_min: int = 2016) -> List[Dict[str, Any]]:
        """
        Busca artigos no Google Scholar via SerpAPI.

        Retorna lista vazia se a chave de API não estiver configurada
        ou se a busca falhar (sem dados fictícios).
        """
        if not self.api_key:
            return []

        cache_key = f"googlescholar_{termo}_{ano_min}"
        cached = cache_medio.get(cache_key)
        if cached is not None:
            return cached

        resultados: List[Dict[str, Any]] = []
        try:
            params = {
                "engine": "google_scholar",
                "q": termo,
                "as_ylo": str(ano_min),
                "as_yhi": str(datetime.now().year),
                "num": "20",
                "api_key": self.api_key,
                "hl": "pt",
            }

            async with httpx.AsyncClient(headers=self.headers, timeout=30) as client:
                response = await client.get(self.SERPAPI_URL, params=params)
                if response.status_code == 200:
                    resultados = self._parse_resultados(response.json(), termo)
                elif response.status_code == 401:
                    print("Google Scholar (SerpAPI): SERPAPI_KEY inválida.")
                elif response.status_code == 429:
                    print("Google Scholar (SerpAPI): cota de buscas esgotada.")
                else:
                    print(f"Google Scholar (SerpAPI): status {response.status_code}")

        except Exception as e:
            print(f"Erro Google Scholar (SerpAPI): {e}")

        cache_medio.set(cache_key, resultados)
        return resultados

    def _parse_resultados(self, data: Dict, termo: str) -> List[Dict[str, Any]]:
        """Converte resposta JSON da SerpAPI para o formato padrão."""
        resultados = []
        organic = data.get("organic_results") or []

        for item in organic:
            try:
                titulo = (item.get("title") or "").strip()
                if not titulo or len(titulo) < 5:
                    continue

                # Publicação (snippet de metadados)
                pub_info = item.get("publication_info") or {}
                authors_raw = pub_info.get("authors") or []
                autores: Optional[List[str]] = None
                if authors_raw:
                    autores = [
                        a.get("name", "").strip()
                        for a in authors_raw
                        if a.get("name")
                    ][:10]

                # Ano extraído do summary da publicação
                ano: Optional[int] = None
                summary = pub_info.get("summary") or ""
                m = re.search(r"(20\d{2})", summary)
                if m:
                    ano = int(m.group(1))

                # Links
                link = item.get("link")
                resources = item.get("resources") or []
                pdf_url: Optional[str] = None
                for r in resources:
                    if r.get("file_format") == "PDF":
                        pdf_url = r.get("link")
                        break

                url = pdf_url or link

                # DOI — presente em alguns resultados
                doi: Optional[str] = None
                inline_links = item.get("inline_links") or {}
                cited_by = inline_links.get("cited_by") or {}
                # DOI não é retornado diretamente; extrair do URL se possível
                if link:
                    doi_match = re.search(r"10\.\d{4,}/\S+", link)
                    if doi_match:
                        doi = doi_match.group(0).rstrip(")")

                # Resumo / snippet
                resumo: Optional[str] = (item.get("snippet") or "").strip() or None
                if resumo and len(resumo) > 3000:
                    resumo = resumo[:3000]

                # Citações
                citation_count: Optional[int] = None
                cited_by_count = cited_by.get("total")
                if cited_by_count is not None:
                    try:
                        citation_count = int(cited_by_count)
                    except (ValueError, TypeError):
                        pass

                # Journal a partir do summary (ex: "Nature, 2023")
                journal: Optional[str] = None
                if summary:
                    partes = [p.strip() for p in summary.split("-")]
                    if partes:
                        journal = partes[0] or None

                resultados.append({
                    "titulo": titulo,
                    "autores": autores if autores else None,
                    "resumo": resumo,
                    "url": url,
                    "fonte": "Google Scholar",
                    "journal": journal,
                    "volume": "",
                    "issue": "",
                    "paginas": "",
                    "tipo": "artigo",
                    "ano": ano,
                    "doi": doi,
                    "pmid": None,
                    "citation_count": citation_count,
                    "keywords": [termo],
                })
            except Exception:
                continue

        return resultados
