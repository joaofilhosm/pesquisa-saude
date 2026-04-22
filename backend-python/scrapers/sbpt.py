"""
Scraper da SBPT - Sociedade Brasileira de Pneumologia e Tisiologia

Busca diretrizes e publicações no site da SBPT.
Nenhum dado é fabricado: se a busca falha, retorna lista vazia.
"""
import httpx
from bs4 import BeautifulSoup
from typing import List, Dict, Any, Optional
from datetime import datetime
import re
import urllib.parse

from .cache import cache_medio


class SBPTScraper:
    """Scraper para protocolos da SBPT"""

    BASE_URL = "https://sbpt.org.br"

    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "pt-BR,pt;q=0.9",
        }

    async def buscar_protocolos(self, termo: str = "") -> List[Dict[str, Any]]:
        """
        Busca diretrizes e publicações no site da SBPT.
        Retorna lista vazia se a busca falhar (sem dados fictícios).
        """
        cache_key = f"sbpt_{termo}"
        cached = cache_medio.get(cache_key)
        if cached is not None:
            return cached

        resultados = []

        urls = []
        if termo:
            urls.append(f"{self.BASE_URL}/?s={urllib.parse.quote(termo)}")
        urls.append(f"{self.BASE_URL}/publicacoes/diretrizes/")
        urls.append(f"{self.BASE_URL}/diretrizes/")

        async with httpx.AsyncClient(
            headers=self.headers, timeout=30, follow_redirects=True
        ) as client:
            for url in urls[:2]:
                try:
                    response = await client.get(url)
                    if response.status_code == 200:
                        novos = self._parse_html(response.text, termo)
                        resultados.extend(novos)
                except Exception as e:
                    print(f"Erro SBPT ({url}): {e}")

        resultados = self._deduplicar(resultados)[:20]
        cache_medio.set(cache_key, resultados)
        return resultados

    def _parse_html(self, html: str, termo: str) -> List[Dict[str, Any]]:
        """Parse do HTML da SBPT (WordPress)"""
        resultados = []
        soup = BeautifulSoup(html, 'lxml')

        itens = (
            soup.select('article')
            or soup.select('.post')
            or soup.select('.diretriz')
            or soup.select('.entry')
        )

        for item in itens:
            try:
                resultado = self._parse_item(item, termo)
                if resultado:
                    resultados.append(resultado)
            except Exception:
                continue

        return resultados

    def _parse_item(self, item, termo: str) -> Optional[Dict[str, Any]]:
        """Parse de um item de resultado da SBPT"""
        titulo_el = (
            item.select_one('h2.entry-title a')
            or item.select_one('h3.entry-title a')
            or item.select_one('.entry-title a')
            or item.select_one('h2 a')
            or item.select_one('h3 a')
            or item.select_one('h4 a')
        )
        if not titulo_el:
            return None

        titulo = titulo_el.get_text(strip=True)
        if not titulo or len(titulo) < 5:
            return None

        link = titulo_el.get('href', '') or ''
        if link and not link.startswith('http'):
            link = f"{self.BASE_URL}{link}"

        resumo_el = (
            item.select_one('.entry-summary')
            or item.select_one('.entry-content p')
            or item.select_one('.excerpt')
            or item.select_one('p')
        )
        resumo = resumo_el.get_text(strip=True)[:1000] if resumo_el else None

        data_el = item.select_one('time[datetime], .entry-date, .date, .published')
        ano = None
        if data_el:
            dt = data_el.get('datetime', '') or data_el.get_text(strip=True)
            ano = self._extrair_ano(dt)
        if not ano:
            ano = self._extrair_ano(str(item))

        return {
            "titulo": titulo,
            "resumo": resumo,
            "url": link or None,
            "fonte": "SBPT",
            "tipo": "diretriz",
            "ano": ano or datetime.now().year,
            "keywords": [termo] if termo else [],
        }

    def _extrair_ano(self, texto: str) -> Optional[int]:
        anos = re.findall(r'(20\d{2})', texto)
        if not anos:
            return None
        anos_validos = [int(a) for a in anos if 2000 <= int(a) <= datetime.now().year]
        return max(anos_validos) if anos_validos else None

    def _deduplicar(self, resultados: List[Dict]) -> List[Dict]:
        vistos = set()
        unicos = []
        for r in resultados:
            chave = r.get("url") or r.get("titulo", "")[:80]
            if chave and chave not in vistos:
                vistos.add(chave)
                unicos.append(r)
        return unicos

    async def buscar_diretriz(self, doenca: str) -> List[Dict[str, Any]]:
        return await self.buscar_protocolos(doenca)
