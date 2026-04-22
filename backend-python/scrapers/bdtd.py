"""
Scraper da BDTD - Biblioteca Digital Brasileira de Teses e Dissertações

Usa o portal VuFind do IBICT (https://bdtd.ibict.br) para localizar
teses e dissertações de pós-graduação brasileiras.

Referência: https://bdtd.ibict.br
Nenhum dado é fabricado: se a busca falha, retorna lista vazia.
"""
import httpx
from bs4 import BeautifulSoup
from typing import List, Dict, Any, Optional
from datetime import datetime
import re
import urllib.parse

from .cache import cache_medio


class BDTDScraper:
    """
    Scraper para a BDTD (Biblioteca Digital Brasileira de Teses e Dissertações)
    via portal VuFind do IBICT.

    Ideal para localizar trabalhos de pós-graduação (mestrado e doutorado)
    depositados em universidades brasileiras.
    """

    SEARCH_URL = "https://bdtd.ibict.br/vufind/Search/Results"
    BASE_URL = "https://bdtd.ibict.br"

    def __init__(self):
        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
            "Connection": "keep-alive",
        }

    async def buscar(self, termo: str, ano_min: int = 2016) -> List[Dict[str, Any]]:
        """
        Busca teses e dissertações na BDTD.
        Retorna lista vazia se a busca falhar (sem dados fictícios).
        """
        cache_key = f"bdtd_{termo}_{ano_min}"
        cached = cache_medio.get(cache_key)
        if cached is not None:
            return cached

        resultados = []
        try:
            resultados = await self._buscar_vufind(termo, ano_min)
        except Exception as e:
            print(f"Erro BDTD: {e}")

        cache_medio.set(cache_key, resultados)
        return resultados

    async def _buscar_vufind(self, termo: str, ano_min: int) -> List[Dict[str, Any]]:
        """Busca via interface VuFind do IBICT."""
        params = {
            "lookfor": termo,
            "type": "AllFields",
            "limit": "20",
            "sort": "relevance",
        }
        if ano_min:
            params["filter[]"] = f'publishDate:[{ano_min} TO *]'

        url = f"{self.SEARCH_URL}?{urllib.parse.urlencode(params)}"

        async with httpx.AsyncClient(
            headers=self.headers, timeout=30, follow_redirects=True
        ) as client:
            response = await client.get(url)
            if response.status_code != 200:
                return []
            return self._parse_vufind_html(response.text, ano_min)

    def _parse_vufind_html(self, html: str, ano_min: int) -> List[Dict[str, Any]]:
        """Parse do HTML do VuFind."""
        resultados = []
        soup = BeautifulSoup(html, "lxml")

        # VuFind usa diferentes templates; cobrir as versões mais comuns
        itens = (
            soup.select(".result")
            or soup.select(".record")
            or soup.select("article.result")
            or soup.select(".search-result")
        )

        for item in itens:
            try:
                resultado = self._parse_item(item, ano_min)
                if resultado:
                    resultados.append(resultado)
            except Exception:
                continue

        return resultados[:20]

    def _parse_item(self, item, ano_min: int) -> Optional[Dict[str, Any]]:
        """Parseia um item de resultado do VuFind."""
        # Título
        titulo_el = (
            item.select_one(".title a")
            or item.select_one("h2 a")
            or item.select_one("h3 a")
            or item.select_one(".record-title a")
            or item.select_one(".resultInner h3 a")
            or item.select_one(".resultInner h2 a")
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
            item.select_one(".author")
            or item.select_one(".authors")
            or item.select_one(".contributor")
        )
        if autor_el:
            texto = autor_el.get_text(separator=";", strip=True)
            autores = [a.strip() for a in re.split(r"[;,]", texto) if a.strip()][:10]

        # Resumo
        resumo_el = item.select_one(".abstract") or item.select_one(".summary")
        resumo = resumo_el.get_text(strip=True)[:2000] if resumo_el else None

        # Ano
        ano: Optional[int] = None
        ano_el = (
            item.select_one(".publishDateContainer")
            or item.select_one(".published")
            or item.select_one(".date")
            or item.select_one(".year")
        )
        if ano_el:
            ano = self._extrair_ano(ano_el.get_text(strip=True))
        if not ano:
            ano = self._extrair_ano(str(item))
        if ano and ano < ano_min:
            return None

        # Tipo de documento
        formato_el = item.select_one(".format") or item.select_one(".recordtype")
        formato_texto = formato_el.get_text(strip=True).lower() if formato_el else ""
        tipo = "dissertacao" if "master" in formato_texto or "mestrado" in formato_texto else "tese"

        # Instituição
        inst_el = item.select_one(".institution") or item.select_one(".publisher")
        journal = inst_el.get_text(strip=True) if inst_el else None

        return {
            "titulo": titulo,
            "autores": autores if autores else None,
            "resumo": resumo,
            "url": link or None,
            "fonte": "BDTD",
            "journal": journal,
            "tipo": tipo,
            "ano": ano or datetime.now().year,
            "doi": None,
            "keywords": [],
        }

    def _extrair_ano(self, texto: str) -> Optional[int]:
        anos = re.findall(r"(20\d{2})", texto)
        if not anos:
            return None
        validos = [int(a) for a in anos if 2000 <= int(a) <= datetime.now().year]
        return max(validos) if validos else None
