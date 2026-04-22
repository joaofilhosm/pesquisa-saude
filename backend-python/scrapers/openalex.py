"""
Scraper do OpenAlex - Base de Dados Aberta de Literatura Científica

OpenAlex é um catálogo aberto e gratuito de mais de 250 milhões de trabalhos
acadêmicos, mantido pela OurResearch. Substitui o extinto Microsoft Academic
e é compatível com os dados do MAG (Microsoft Academic Graph).

API pública sem autenticação:
  GET https://api.openalex.org/works?search=<termo>

Polite pool: incluir e-mail no User-Agent reduz latência e aumenta rate limit.
Documentação: https://docs.openalex.org/api-reference/works
"""
import httpx
from typing import List, Dict, Any, Optional

from .cache import cache_medio


class OpenAlexScraper:
    """
    Scraper para OpenAlex via REST API oficial.

    Características:
    - 100% gratuito e sem autenticação
    - 250M+ trabalhos acadêmicos (maior base aberta do mundo)
    - Retorna cited_by_count, open access URL e metadados completos
    - Polite pool: e-mail no User-Agent melhora rate limits automaticamente
    """

    API_URL = "https://api.openalex.org/works"
    MAILTO = "pesquisa-saude@github.com"

    def __init__(self):
        self.headers = {
            "User-Agent": (
                "PesquisaSaude/3.0 (https://github.com/joaofilhosm/pesquisa-saude; "
                f"mailto:{self.MAILTO})"
            ),
            "Accept": "application/json",
        }

    async def buscar(self, termo: str, ano_min: int = 2016) -> List[Dict[str, Any]]:
        """
        Busca trabalhos no OpenAlex via REST API.

        Retorna lista vazia se a busca falhar (sem dados fictícios).
        """
        cache_key = f"openalex_{termo}_{ano_min}"
        cached = cache_medio.get(cache_key)
        if cached is not None:
            return cached

        resultados: List[Dict[str, Any]] = []
        try:
            params = {
                "search": termo,
                "filter": f"publication_year:>{ano_min - 1}",
                "per-page": 20,
                "sort": "cited_by_count:desc",
                "select": (
                    "title,abstract_inverted_index,doi,authorships,"
                    "publication_year,cited_by_count,"
                    "primary_location,type,id"
                ),
                "mailto": self.MAILTO,
            }

            async with httpx.AsyncClient(headers=self.headers, timeout=30) as client:
                response = await client.get(self.API_URL, params=params)
                if response.status_code == 200:
                    resultados = self._parse_resultados(response.json(), termo)
                elif response.status_code == 429:
                    print("OpenAlex: rate limit atingido.")
                else:
                    print(f"OpenAlex: status {response.status_code}")

        except Exception as e:
            print(f"Erro OpenAlex: {e}")

        cache_medio.set(cache_key, resultados)
        return resultados

    def _abstract_from_inverted_index(
        self, inverted_index: Optional[Dict[str, List[int]]]
    ) -> Optional[str]:
        """
        Converte o abstract_inverted_index do OpenAlex para texto simples.

        O OpenAlex armazena abstracts como índice invertido: {palavra: [posições]}.
        Esta função reconstrói o texto original a partir das posições.
        """
        if not inverted_index:
            return None
        positions: Dict[int, str] = {}
        for word, pos_list in inverted_index.items():
            for pos in pos_list:
                positions[pos] = word
        if not positions:
            return None
        texto = " ".join(positions[i] for i in sorted(positions))
        return texto[:3000] if texto else None

    def _parse_resultados(self, data: Dict, termo: str) -> List[Dict[str, Any]]:
        """Converte a resposta JSON do OpenAlex para o formato padrão do projeto."""
        resultados = []
        works = data.get("results") or []

        for work in works:
            try:
                titulo = (work.get("title") or "").strip()
                if not titulo or len(titulo) < 5:
                    continue

                # Autores via authorships
                autores: Optional[List[str]] = None
                authorships = work.get("authorships") or []
                if authorships:
                    autores = [
                        a.get("author", {}).get("display_name", "").strip()
                        for a in authorships[:10]
                        if a.get("author", {}).get("display_name")
                    ] or None

                # DOI
                doi_raw = work.get("doi") or ""
                doi: Optional[str] = None
                if doi_raw:
                    # OpenAlex retorna "https://doi.org/10.xxx/yyy" — extrair só o DOI
                    doi = doi_raw.replace("https://doi.org/", "").strip() or None

                # URL — preferir open access, fallback para DOI
                primary = work.get("primary_location") or {}
                url: Optional[str] = (
                    primary.get("landing_page_url")
                    or (f"https://doi.org/{doi}" if doi else None)
                )

                # URL de acesso aberto (PDF ou página)
                oa_url: Optional[str] = primary.get("pdf_url") or None

                # Journal / periódico
                source = primary.get("source") or {}
                journal: Optional[str] = source.get("display_name") or None

                # Ano
                ano: Optional[int] = work.get("publication_year")

                # Resumo
                resumo = self._abstract_from_inverted_index(
                    work.get("abstract_inverted_index")
                )

                # Citações
                citation_count: Optional[int] = work.get("cited_by_count")

                # Tipo mapeado
                work_type = (work.get("type") or "article").lower()
                tipo_map = {
                    "article": "artigo",
                    "review": "artigo",
                    "book-chapter": "artigo",
                    "dissertation": "tese",
                    "book": "artigo",
                    "dataset": None,
                    "other": "artigo",
                }
                tipo = tipo_map.get(work_type, "artigo")
                if tipo is None:
                    continue

                # ID OpenAlex (ex: W2741809807)
                openalex_id = (work.get("id") or "").replace(
                    "https://openalex.org/", ""
                ) or None

                resultados.append({
                    "id": openalex_id,
                    "titulo": titulo,
                    "autores": autores,
                    "resumo": resumo,
                    "url": oa_url or url,
                    "fonte": "OpenAlex",
                    "journal": journal,
                    "volume": "",
                    "issue": "",
                    "paginas": "",
                    "tipo": tipo,
                    "ano": ano,
                    "doi": doi,
                    "pmid": None,
                    "citation_count": citation_count,
                    "keywords": [termo],
                })
            except Exception:
                continue

        return resultados
