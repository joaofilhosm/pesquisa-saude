"""
Scraper da SBC - Sociedade Brasileira de Cardiologia

Busca diretrizes, posicionamentos e publicações no site da SBC/Arquivos Brasileiros de Cardiologia.
Nenhum dado é fabricado: se a busca falha, retorna lista vazia.
"""
import httpx
from bs4 import BeautifulSoup
from typing import List, Dict, Any, Optional
from datetime import datetime
import re
import urllib.parse

from .cache import cache_medio


class SBCScraper:
    """Scraper para protocolos e diretrizes da SBC"""

    BASE_URL = "https://www.cardiol.br"
    # Publicações científicas da SBC (Arquivos Brasileiros de Cardiologia)
    ABC_URL = "https://abccardiol.org"
    # Portal de diretrizes
    DIRETRIZES_URL = "https://www.cardiol.br/publicacoes/diretrizes"

    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "pt-BR,pt;q=0.9",
        }

    async def buscar_protocolos(self, termo: str = "") -> List[Dict[str, Any]]:
        """
        Busca diretrizes e publicações da SBC.
        Retorna lista vazia se a busca falhar (sem dados fictícios).
        """
        cache_key = f"sbc_{termo}"
        cached = cache_medio.get(cache_key)
        if cached is not None:
            return cached

        resultados = []

        # Tentar Arquivos Brasileiros de Cardiologia (revista científica)
        try:
            resultados_abc = await self._buscar_abc(termo)
            resultados.extend(resultados_abc)
        except Exception as e:
            print(f"Erro SBC/ABC: {e}")

        # Tentar site principal da SBC
        if not resultados and termo:
            try:
                url = f"{self.BASE_URL}/busca/?q={urllib.parse.quote(termo)}"
                async with httpx.AsyncClient(
                    headers=self.headers, timeout=30, follow_redirects=True
                ) as client:
                    response = await client.get(url)
                    if response.status_code == 200:
                        resultados = self._parse_html(response.text, termo)
            except Exception as e:
                print(f"Erro SBC site: {e}")

        resultados = self._deduplicar(resultados)[:20]
        cache_medio.set(cache_key, resultados)
        return resultados

    async def _buscar_abc(self, termo: str) -> List[Dict[str, Any]]:
        """Busca nos Arquivos Brasileiros de Cardiologia (ABC)"""
        if not termo:
            url = f"{self.ABC_URL}/"
        else:
            url = f"{self.ABC_URL}/?s={urllib.parse.quote(termo)}"

        async with httpx.AsyncClient(
            headers=self.headers, timeout=30, follow_redirects=True
        ) as client:
            response = await client.get(url)
            if response.status_code != 200:
                return []
            return self._parse_html(response.text, termo, fonte="SBC/ABC Cardiol")

    def _parse_html(self, html: str, termo: str, fonte: str = "SBC") -> List[Dict[str, Any]]:
        """Parse do HTML da SBC"""
        resultados = []
        soup = BeautifulSoup(html, 'lxml')

        itens = (
            soup.select('article')
            or soup.select('.post')
            or soup.select('.diretriz-item')
            or soup.select('.entry')
        )

        for item in itens:
            try:
                resultado = self._parse_item(item, termo, fonte)
                if resultado:
                    resultados.append(resultado)
            except Exception:
                continue

        return resultados

    def _parse_item(self, item, termo: str, fonte: str = "SBC") -> Optional[Dict[str, Any]]:
        """Parse de um item de resultado da SBC"""
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
            base = self.ABC_URL if 'abccardiol' in link else self.BASE_URL
            link = f"{base}{link}"

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

        doi = self._extrair_doi(str(item))

        return {
            "titulo": titulo,
            "resumo": resumo,
            "url": link or None,
            "fonte": fonte,
            "tipo": "diretriz",
            "ano": ano or datetime.now().year,
            "doi": doi,
            "keywords": [termo] if termo else [],
        }

    def _extrair_ano(self, texto: str) -> Optional[int]:
        anos = re.findall(r'(20\d{2})', texto)
        if not anos:
            return None
        anos_validos = [int(a) for a in anos if 2000 <= int(a) <= datetime.now().year]
        return max(anos_validos) if anos_validos else None

    def _extrair_doi(self, texto: str) -> Optional[str]:
        match = re.search(r'10\.\d{4,}/\S+', texto)
        if match:
            return match.group(0).rstrip('.,;)')
        return None

    def _deduplicar(self, resultados: List[Dict]) -> List[Dict]:
        vistos = set()
        unicos = []
        for r in resultados:
            chave = r.get("url") or r.get("doi") or r.get("titulo", "")[:80]
            if chave and chave not in vistos:
                vistos.add(chave)
                unicos.append(r)
        return unicos

    async def buscar_urgencia_cardio(self) -> List[Dict[str, Any]]:
        return await self.buscar_protocolos("urgência emergência cardiovascular")
