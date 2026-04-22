"""
Scraper da Cochrane Library - Revisões Sistemáticas e Meta-análises

Usa a API pública do Europe PMC (EBI) para buscar conteúdo Cochrane:
  - SRC:CBA → Cochrane Reviews (CDSR)
  - SRC:CTX → Cochrane Protocols

Referência: https://europepmc.org/RestfulWebService
Sem autenticação necessária (acesso público gratuito).
"""
import httpx
import re
from typing import List, Dict, Any, Optional
from datetime import datetime

from .cache import cache_medio


class CochraneScraper:
    """
    Scraper para Cochrane Library via Europe PMC REST API.

    Foca em revisões sistemáticas e meta-análises — o padrão-ouro da
    medicina baseada em evidências.  Zero dados fabricados.
    """

    EUROPEPMC_URL = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"

    def __init__(self):
        self.headers = {
            "User-Agent": "PesquisaSaude/3.0 (https://github.com/joaofilhosm/pesquisa-saude)",
            "Accept": "application/json",
        }

    async def buscar(self, termo: str, ano_min: int = 2016) -> List[Dict[str, Any]]:
        """
        Busca revisões sistemáticas e protocolos da Cochrane via Europe PMC.

        Retorna lista vazia se a busca falhar (sem dados fictícios).
        """
        cache_key = f"cochrane_{termo}_{ano_min}"
        cached = cache_medio.get(cache_key)
        if cached is not None:
            return cached

        resultados = []
        try:
            ano_atual = datetime.now().year
            # SRC:CBA = Cochrane Reviews; SRC:CTX = Cochrane Protocols
            query = (
                f"({termo}) AND (SRC:CBA OR SRC:CTX) "
                f"AND PUB_YEAR:[{ano_min} TO {ano_atual}]"
            )
            params = {
                "query": query,
                "format": "json",
                "resulttype": "core",
                "pageSize": 15,
                "sort": "RELEVANCE",
            }
            async with httpx.AsyncClient(headers=self.headers, timeout=30) as client:
                response = await client.get(self.EUROPEPMC_URL, params=params)
                if response.status_code == 200:
                    resultados = self._parse_resultados(response.json(), termo)
        except Exception as e:
            print(f"Erro Cochrane (EuropePMC): {e}")

        cache_medio.set(cache_key, resultados)
        return resultados

    def _parse_resultados(self, data: Dict, termo: str) -> List[Dict[str, Any]]:
        """Converte a resposta JSON do EuropePMC para o formato padrão."""
        resultados = []
        for item in data.get("resultList", {}).get("result", []):
            try:
                titulo = (item.get("title") or "").strip().rstrip(".")
                if not titulo or len(titulo) < 5:
                    continue

                autores_raw = item.get("authorString") or ""
                autores = [a.strip() for a in re.split(r",\s*", autores_raw) if a.strip()][:10]

                doi = item.get("doi") or None
                pmid = item.get("pmid") or None

                ano_raw = (
                    item.get("pubYear")
                    or (item.get("firstPublicationDate") or "")[:4]
                )
                try:
                    ano = int(ano_raw) if ano_raw else None
                except ValueError:
                    ano = None

                journal = (
                    item.get("journalTitle")
                    or "Cochrane Database of Systematic Reviews"
                )
                resumo = (item.get("abstractText") or "").strip()
                resumo = resumo[:3000] if resumo else None

                url: Optional[str] = None
                if doi:
                    url = f"https://doi.org/{doi}"
                elif pmid:
                    url = f"https://www.ncbi.nlm.nih.gov/pubmed/{pmid}"

                resultados.append({
                    "titulo": titulo,
                    "autores": autores if autores else None,
                    "resumo": resumo,
                    "url": url,
                    "fonte": "Cochrane",
                    "journal": journal,
                    "tipo": "revisao_sistematica",
                    "ano": ano,
                    "doi": doi,
                    "pmid": pmid,
                    "keywords": ["systematic review", "cochrane", termo],
                })
            except Exception:
                continue
        return resultados
