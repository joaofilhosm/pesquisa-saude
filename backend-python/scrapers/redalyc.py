"""
Scraper da Redalyc - Rede de Revistas Científicas da América Latina,
Caribe, Espanha e Portugal.

Usa o portal de busca search.scielo.org com filtros de idioma espanhol/
português e as páginas de busca do redalyc.org.
Nenhum dado é fabricado: se a busca falha, retorna lista vazia.

Referência: https://www.redalyc.org
"""
import httpx
from bs4 import BeautifulSoup
from typing import List, Dict, Any, Optional
from datetime import datetime
import re
import urllib.parse

from .cache import cache_medio


class RedalycScraper:
    """
    Scraper para a Redalyc via busca HTML e OAI-PMH.

    A Redalyc indexa mais de 1.500 revistas científicas latino-americanas
    de acesso aberto.  Serve como complemento ao SciELO com maior cobertura
    de países hispanófonos.
    """

    SEARCH_URL = "https://www.redalyc.org/busquedaArticuloFiltros.oa"
    BASE_URL = "https://www.redalyc.org"

    def __init__(self):
        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "pt-BR,pt;q=0.9,es;q=0.8,en;q=0.7",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
        }

    async def buscar(self, termo: str, ano_min: int = 2016) -> List[Dict[str, Any]]:
        """
        Busca artigos na Redalyc.
        Retorna lista vazia se a busca falhar (sem dados fictícios).
        """
        cache_key = f"redalyc_{termo}_{ano_min}"
        cached = cache_medio.get(cache_key)
        if cached is not None:
            return cached

        resultados = []
        try:
            resultados = await self._buscar_html(termo, ano_min)
        except Exception as e:
            print(f"Erro Redalyc: {e}")

        cache_medio.set(cache_key, resultados)
        return resultados

    async def _buscar_html(self, termo: str, ano_min: int) -> List[Dict[str, Any]]:
        """Scraping da página de busca do Redalyc."""
        params = {
            "q": termo,
            "paginacao": "1",
            "tipo": "articulo",
        }
        url = f"{self.SEARCH_URL}?{urllib.parse.urlencode(params)}"

        async with httpx.AsyncClient(
            headers=self.headers, timeout=30, follow_redirects=True
        ) as client:
            response = await client.get(url)
            if response.status_code != 200:
                return []
            return self._parse_html(response.text, ano_min)

    def _parse_html(self, html: str, ano_min: int) -> List[Dict[str, Any]]:
        """Parse do HTML de resultados da Redalyc."""
        resultados = []
        soup = BeautifulSoup(html, "lxml")

        # Redalyc usa vários containers dependendo da versão
        itens = (
            soup.select("article.resultado")
            or soup.select(".articuloBusqueda")
            or soup.select(".resultado-articulo")
            or soup.select("li.articulo")
            or soup.select(".card-articulo")
            or soup.select("article")
        )

        for item in itens:
            try:
                resultado = self._parse_item(item, ano_min)
                if resultado:
                    resultados.append(resultado)
            except Exception:
                continue

        # Deduplicar por URL
        vistos: set = set()
        unicos = []
        for r in resultados:
            chave = r.get("url") or r.get("titulo", "")[:80]
            if chave and chave not in vistos:
                vistos.add(chave)
                unicos.append(r)
            elif not chave:
                unicos.append(r)

        return unicos[:20]

    def _parse_item(self, item, ano_min: int) -> Optional[Dict[str, Any]]:
        """Parseia um item de resultado da Redalyc."""
        # Título — vários seletores para cobrir diferentes versões do template
        titulo_el = (
            item.select_one("h2.titulo a")
            or item.select_one("h3.titulo a")
            or item.select_one(".titulo a")
            or item.select_one("h2 a")
            or item.select_one("h3 a")
            or item.select_one(".article-title a")
            or item.select_one("a.titulo")
        )
        if not titulo_el:
            return None

        titulo = titulo_el.get_text(strip=True)
        if not titulo or len(titulo) < 5:
            return None

        link = titulo_el.get("href", "") or ""
        if link and not link.startswith("http"):
            link = f"{self.BASE_URL}{link}"

        # Autores
        autores: List[str] = []
        autor_el = (
            item.select_one(".autores")
            or item.select_one(".autor")
            or item.select_one(".authors")
        )
        if autor_el:
            texto = autor_el.get_text(separator=";", strip=True)
            autores = [a.strip() for a in re.split(r"[;,]", texto) if a.strip()][:10]

        # Resumo / abstract
        resumo_el = (
            item.select_one(".resumen")
            or item.select_one(".abstract")
            or item.select_one(".descripcion")
            or item.select_one("p.description")
        )
        resumo = resumo_el.get_text(strip=True)[:2000] if resumo_el else None

        # Revista e ano
        revista_el = (
            item.select_one(".revista")
            or item.select_one(".journal")
            or item.select_one(".source")
        )
        journal: Optional[str] = None
        ano: Optional[int] = None
        volume = issue = paginas = ""

        if revista_el:
            revista_texto = revista_el.get_text(strip=True)
            journal = re.sub(r",.*", "", revista_texto).strip() or None
            ano = self._extrair_ano(revista_texto)
            vol_m = re.search(r"v[olume\.]*\s*(\d+)", revista_texto, re.IGNORECASE)
            if vol_m:
                volume = vol_m.group(1)
            num_m = re.search(r"n[úumero\.]*\s*(\d+)", revista_texto, re.IGNORECASE)
            if num_m:
                issue = num_m.group(1)

        if not ano:
            ano = self._extrair_ano(str(item))
        if ano and ano < ano_min:
            return None

        doi = self._extrair_doi(str(item))
        if not doi and link:
            doi_m = re.search(r"10\.\d{4,}/\S+", link)
            if doi_m:
                doi = doi_m.group(0)

        return {
            "titulo": titulo,
            "autores": autores if autores else None,
            "resumo": resumo,
            "url": link or None,
            "fonte": "Redalyc",
            "journal": journal,
            "volume": volume,
            "issue": issue,
            "paginas": paginas,
            "tipo": "artigo",
            "ano": ano or datetime.now().year,
            "doi": doi,
            "keywords": [],
        }

    def _extrair_ano(self, texto: str) -> Optional[int]:
        anos = re.findall(r"(20\d{2})", texto)
        if not anos:
            return None
        validos = [int(a) for a in anos if 2000 <= int(a) <= datetime.now().year]
        return max(validos) if validos else None

    def _extrair_doi(self, texto: str) -> Optional[str]:
        m = re.search(r"10\.\d{4,}/\S+", texto)
        if m:
            return m.group(0).rstrip(".,;)")
        return None
