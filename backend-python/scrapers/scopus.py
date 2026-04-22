"""
Scraper da Scopus - Base de Dados de Citações da Elsevier

Usa a API oficial da Elsevier (Scopus Search API) para retornar artigos
com metadados ricos: DOI, autores, journal, resumo, contagem de citações.

Requer variável de ambiente ELSEVIER_API_KEY.
Sem a chave configurada, o scraper retorna lista vazia sem erros.

Referências:
  - https://dev.elsevier.com/documentation/SCOPUSSearchAPI.wadl
  - https://api.elsevier.com/content/search/scopus
"""
import httpx
import os
import re
from typing import List, Dict, Any, Optional
from datetime import datetime

from .cache import cache_medio


class ScopusScraper:
    """
    Scraper para Scopus via Elsevier Search API.

    Uma das maiores bases de dados de resumos e citações do mundo,
    cobrindo mais de 25.000 títulos de 5.000 editoras.

    Requer ELSEVIER_API_KEY no .env — obtida gratuitamente em:
    https://dev.elsevier.com/
    """

    SCOPUS_URL = "https://api.elsevier.com/content/search/scopus"

    def __init__(self):
        self.api_key = os.getenv("ELSEVIER_API_KEY")
        self.inst_token = os.getenv("ELSEVIER_INST_TOKEN")  # opcional
        self.headers = {
            "User-Agent": "PesquisaSaude/3.0 (https://github.com/joaofilhosm/pesquisa-saude)",
            "Accept": "application/json",
        }
        if self.api_key:
            self.headers["X-ELS-APIKey"] = self.api_key
        if self.inst_token:
            self.headers["X-ELS-Insttoken"] = self.inst_token

    async def buscar(self, termo: str, ano_min: int = 2016) -> List[Dict[str, Any]]:
        """
        Busca artigos na Scopus via Elsevier API.

        Retorna lista vazia se a chave de API não estiver configurada
        ou se a busca falhar (sem dados fictícios).
        """
        if not self.api_key:
            # Sem API key, não há como acessar a Scopus
            return []

        cache_key = f"scopus_{termo}_{ano_min}"
        cached = cache_medio.get(cache_key)
        if cached is not None:
            return cached

        resultados = []
        try:
            ano_atual = datetime.now().year
            # Scopus Query Language: TITLE-ABS-KEY para busca completa
            query = f"TITLE-ABS-KEY({termo}) AND PUBYEAR > {ano_min - 1}"
            params = {
                "query": query,
                "count": "20",
                "start": "0",
                "sort": "relevancy",
                "date": f"{ano_min}-{ano_atual}",
                "field": (
                    "dc:title,dc:creator,prism:publicationName,"
                    "prism:coverDate,dc:description,prism:doi,"
                    "prism:volume,prism:issueIdentifier,"
                    "prism:pageRange,prism:url,dc:identifier"
                ),
            }

            async with httpx.AsyncClient(
                headers=self.headers, timeout=30
            ) as client:
                response = await client.get(self.SCOPUS_URL, params=params)
                if response.status_code == 200:
                    resultados = self._parse_resultados(response.json(), termo)
                elif response.status_code == 401:
                    print("Scopus: API key inválida ou sem permissão.")
                elif response.status_code == 429:
                    print("Scopus: rate limit atingido.")
                else:
                    print(f"Scopus: status {response.status_code}")

        except Exception as e:
            print(f"Erro Scopus: {e}")

        cache_medio.set(cache_key, resultados)
        return resultados

    def _parse_resultados(self, data: Dict, termo: str) -> List[Dict[str, Any]]:
        """Converte a resposta JSON da Scopus API para o formato padrão."""
        resultados = []
        entries = (
            data.get("search-results", {}).get("entry", [])
            or data.get("entry", [])
        )

        for item in entries:
            try:
                titulo = (item.get("dc:title") or "").strip()
                if not titulo or len(titulo) < 5:
                    continue

                # Autores — campo dc:creator é a lista de autores como string
                autores_raw = item.get("dc:creator") or ""
                autores = [
                    a.strip() for a in re.split(r";|,(?=[A-Z])", autores_raw)
                    if a.strip()
                ][:10]

                doi = item.get("prism:doi") or None
                url = item.get("prism:url") or (
                    f"https://doi.org/{doi}" if doi else None
                )

                # Ano de publicação
                cover_date = item.get("prism:coverDate") or ""
                ano: Optional[int] = None
                if cover_date:
                    m = re.search(r"(20\d{2})", cover_date)
                    if m:
                        ano = int(m.group(1))

                journal = item.get("prism:publicationName") or None
                volume = item.get("prism:volume") or ""
                issue = item.get("prism:issueIdentifier") or ""
                paginas = item.get("prism:pageRange") or ""

                resumo = (item.get("dc:description") or "").strip()
                resumo = resumo[:3000] if resumo else None

                # Scopus ID
                scopus_id = item.get("dc:identifier") or ""

                resultados.append({
                    "titulo": titulo,
                    "autores": autores if autores else None,
                    "resumo": resumo,
                    "url": url,
                    "fonte": "Scopus",
                    "journal": journal,
                    "volume": volume,
                    "issue": issue,
                    "paginas": paginas,
                    "tipo": "artigo",
                    "ano": ano,
                    "doi": doi,
                    "id": scopus_id if scopus_id else None,
                    "keywords": [termo],
                })
            except Exception:
                continue

        return resultados
