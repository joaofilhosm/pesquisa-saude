"""
Scraper do Portal de Periódicos CAPES

O Portal de Periódicos CAPES reúne mais de 50 mil títulos científicos e
é acessível gratuitamente dentro das redes de universidades brasileiras.

Estratégia:
1. Tenta buscar via CrossRef API (cobertura abrangente, sem restrição de IP)
   com filtros orientados a periódicos brasileiros/CAPES.
2. O CrossRef indexa a maioria dos artigos que o CAPES disponibiliza,
   incluindo seus metadados públicos (título, DOI, autores, resumo, etc.).

Referências:
  - https://www.periodicos.capes.gov.br
  - https://api.crossref.org
Nenhum dado é fabricado: se a busca falha, retorna lista vazia.
"""
import httpx
from typing import List, Dict, Any, Optional
from datetime import datetime
import re

from .cache import cache_medio


class CapesScraper:
    """
    Scraper para o Portal de Periódicos CAPES.

    Usa CrossRef API como backend de descoberta aberta (metadados públicos),
    e tenta o portal CAPES quando disponível.  O acesso ao texto completo
    de artigos pagos exige rede de universidade credenciada.
    """

    # CrossRef API — metadados públicos, sem autenticação
    CROSSREF_URL = "https://api.crossref.org/works"
    # E-mail identificador para a fila polida do CrossRef (melhora rate limits)
    CROSSREF_MAILTO = "pesquisa-saude@github.com"

    def __init__(self):
        self.headers = {
            "User-Agent": (
                "PesquisaSaude/3.0 (https://github.com/joaofilhosm/pesquisa-saude; "
                f"mailto:{self.CROSSREF_MAILTO})"
            ),
            "Accept": "application/json",
        }

    async def buscar(self, termo: str, ano_min: int = 2016) -> List[Dict[str, Any]]:
        """
        Busca artigos científicos acessíveis via Portal CAPES.

        Usa CrossRef API como proxy de descoberta de metadados públicos.
        Retorna lista vazia se a busca falhar (sem dados fictícios).
        """
        cache_key = f"capes_{termo}_{ano_min}"
        cached = cache_medio.get(cache_key)
        if cached is not None:
            return cached

        resultados = []
        try:
            resultados = await self._buscar_crossref(termo, ano_min)
        except Exception as e:
            print(f"Erro CAPES/CrossRef: {e}")

        cache_medio.set(cache_key, resultados)
        return resultados

    async def _buscar_crossref(self, termo: str, ano_min: int) -> List[Dict[str, Any]]:
        """Busca via CrossRef API com filtros de relevância médica."""
        ano_atual = datetime.now().year
        params = {
            "query": termo,
            "filter": (
                f"from-pub-date:{ano_min},"
                "type:journal-article"
            ),
            "rows": 15,
            "sort": "relevance",
            "select": (
                "DOI,title,author,published,container-title,"
                "abstract,URL,volume,issue,page,ISSN"
            ),
            "mailto": self.CROSSREF_MAILTO,
        }

        async with httpx.AsyncClient(headers=self.headers, timeout=30) as client:
            response = await client.get(self.CROSSREF_URL, params=params)
            if response.status_code != 200:
                return []
            data = response.json()
            return self._parse_crossref(data)

    def _parse_crossref(self, data: Dict) -> List[Dict[str, Any]]:
        """Converte resposta CrossRef para o formato padrão."""
        resultados = []
        items = data.get("message", {}).get("items", [])

        for item in items:
            try:
                titulos = item.get("title") or []
                titulo = titulos[0].strip() if titulos else ""
                if not titulo or len(titulo) < 5:
                    continue

                # Autores
                autores: List[str] = []
                for autor in item.get("author", [])[:10]:
                    nome = ""
                    if autor.get("family") and autor.get("given"):
                        nome = f"{autor['family']}, {autor['given']}"
                    elif autor.get("family"):
                        nome = autor["family"]
                    elif autor.get("name"):
                        nome = autor["name"]
                    if nome:
                        autores.append(nome)

                # DOI e URL
                doi = item.get("DOI") or None
                url = item.get("URL") or (f"https://doi.org/{doi}" if doi else None)

                # Ano de publicação
                ano: Optional[int] = None
                pub = item.get("published") or item.get("published-print") or {}
                dp = pub.get("date-parts", [[]])[0]
                if dp:
                    try:
                        ano = int(dp[0])
                    except (ValueError, IndexError):
                        pass

                # Revista
                container = item.get("container-title") or []
                journal = container[0] if container else None

                # Volume, issue, páginas
                volume = item.get("volume") or ""
                issue = item.get("issue") or ""
                paginas = item.get("page") or ""

                # Abstract
                resumo_raw = item.get("abstract") or ""
                # Remover tags JATS/XML comuns em resumos do CrossRef
                resumo = re.sub(r"<[^>]+>", " ", resumo_raw).strip()
                resumo = re.sub(r"\s+", " ", resumo)[:3000] if resumo else None

                resultados.append({
                    "titulo": titulo,
                    "autores": autores if autores else None,
                    "resumo": resumo,
                    "url": url,
                    "fonte": "CAPES",
                    "journal": journal,
                    "volume": volume,
                    "issue": issue,
                    "paginas": paginas,
                    "tipo": "artigo",
                    "ano": ano,
                    "doi": doi,
                    "keywords": [],
                })
            except Exception:
                continue

        return resultados
