"""
Scraper da SBMFC - Sociedade Brasileira de Medicina de Família e Comunidade

Busca protocolos, diretrizes e publicações no site da SBMFC.
Nenhum dado é fabricado: se a busca falha, retorna lista vazia.
"""
import httpx
from bs4 import BeautifulSoup
from typing import List, Dict, Any, Optional
from datetime import datetime
import re
import urllib.parse

from .cache import cache_medio


class SBMFCScraper:
    """Scraper para protocolos da SBMFC"""

    BASE_URL = "https://www.sbmfc.org.br"

    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "pt-BR,pt;q=0.9",
        }

    async def buscar_protocolos(self, termo: str = "") -> List[Dict[str, Any]]:
        """
        Busca protocolos e publicações no site da SBMFC.
        Retorna lista vazia se a busca falhar (sem dados fictícios).
        """
        cache_key = f"sbmfc_{termo}"
        cached = cache_medio.get(cache_key)
        if cached is not None:
            return cached

        resultados = []

        urls_para_buscar = []
        if termo:
            urls_para_buscar.append(f"{self.BASE_URL}/?s={urllib.parse.quote(termo)}")
        urls_para_buscar.append(f"{self.BASE_URL}/publicacoes/")
        urls_para_buscar.append(f"{self.BASE_URL}/normas-e-recomendacoes/")

        async with httpx.AsyncClient(
            headers=self.headers, timeout=30, follow_redirects=True
        ) as client:
            for url in urls_para_buscar[:2]:  # Máximo 2 URLs por busca
                try:
                    response = await client.get(url)
                    if response.status_code == 200:
                        novos = self._parse_html(response.text, termo)
                        resultados.extend(novos)
                except Exception as e:
                    print(f"Erro SBMFC ({url}): {e}")

        resultados = self._deduplicar(resultados)[:20]
        cache_medio.set(cache_key, resultados)
        return resultados

    def _parse_html(self, html: str, termo: str) -> List[Dict[str, Any]]:
        """Parse do HTML da SBMFC (WordPress)"""
        resultados = []
        soup = BeautifulSoup(html, 'lxml')

        # WordPress usa 'article' ou '.post' como container de posts
        itens = (
            soup.select('article.post')
            or soup.select('article')
            or soup.select('.post')
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
        """Parse de um item de post WordPress da SBMFC"""
        titulo_el = (
            item.select_one('h2.entry-title a')
            or item.select_one('h3.entry-title a')
            or item.select_one('.entry-title a')
            or item.select_one('h2 a')
            or item.select_one('h3 a')
        )
        if not titulo_el:
            return None

        titulo = titulo_el.get_text(strip=True)
        if not titulo or len(titulo) < 5:
            return None

        link = titulo_el.get('href', '') or ''

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

        categorias = []
        for cat_el in item.select('.cat-item, .category a, [rel="category tag"]'):
            cat = cat_el.get_text(strip=True)
            if cat:
                categorias.append(cat)

        return {
            "titulo": titulo,
            "resumo": resumo,
            "url": link or None,
            "fonte": "SBMFC",
            "tipo": "protocolo",
            "ano": ano or datetime.now().year,
            "keywords": categorias[:5] + ([termo] if termo else []),
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

    async def buscar_protocolos_ubs(self) -> List[Dict[str, Any]]:
        return await self.buscar_protocolos("atenção primária")

    async def buscar_prescricao(self) -> List[Dict[str, Any]]:
        return await self.buscar_protocolos("prescrição")
