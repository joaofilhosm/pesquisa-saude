"""
Scraper da LILACS - Literatura Latino-Americana em Ciências da Saúde

Usa o portal de busca BVS (Biblioteca Virtual em Saúde) que indexa LILACS.
Nenhum dado é fabricado: se a busca falha, retorna lista vazia.
"""
import httpx
from bs4 import BeautifulSoup
from typing import List, Dict, Any, Optional
from datetime import datetime
import re
import urllib.parse

from .cache import cache_medio


class LILACSScraper:
    """Scraper para base LILACS via portal BVS"""

    # Portal BVS - busca integrada com LILACS e outras bases
    BVS_SEARCH_URL = "https://pesquisa.bvsalud.org/portal/resource/pt/"
    # iAHx direto da BIREME
    BIREME_URL = "https://bases.bireme.br/cgi-bin/wxislind.exe/iah/online/"

    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
        }

    async def buscar(self, termo: str, ano_min: int = 2016) -> List[Dict[str, Any]]:
        """
        Busca artigos reais na LILACS via BVS.
        Retorna lista vazia se a busca falhar (sem dados fictícios).
        """
        cache_key = f"lilacs_{termo}_{ano_min}"
        cached = cache_medio.get(cache_key)
        if cached is not None:
            return cached

        resultados = []

        # Tentar portal BVS primeiro
        try:
            resultados = await self._buscar_bvs_portal(termo, ano_min)
        except Exception as e:
            print(f"Erro LILACS (BVS portal): {e}")

        # Se o portal BVS falhou, tentar a iAHx BIREME
        if not resultados:
            try:
                resultados = await self._buscar_bireme_iah(termo, ano_min)
            except Exception as e:
                print(f"Erro LILACS (BIREME iAHx): {e}")

        cache_medio.set(cache_key, resultados)
        return resultados

    async def _buscar_bvs_portal(self, termo: str, ano_min: int) -> List[Dict[str, Any]]:
        """Busca no portal BVS principal"""
        query = urllib.parse.quote(f"{termo} AND db:LILACS AND year_cluster:[{ano_min} TO *]")
        url = f"{self.BVS_SEARCH_URL}?q={query}&lang=pt&count=20"

        async with httpx.AsyncClient(
            headers=self.headers, timeout=30, follow_redirects=True
        ) as client:
            response = await client.get(url)
            if response.status_code != 200:
                return []
            return self._parse_bvs_html(response.text, ano_min)

    async def _buscar_bireme_iah(self, termo: str, ano_min: int) -> List[Dict[str, Any]]:
        """Busca na interface iAHx da BIREME"""
        params = {
            "IsisScript": "iah/iah.xis",
            "base": "LILACS",
            "lang": "p",
            "nextAction": "search",
            "exprSearch": termo,
            "indexSearch": "KW",
        }
        url = f"{self.BIREME_URL}?{urllib.parse.urlencode(params)}"

        async with httpx.AsyncClient(
            headers=self.headers, timeout=30, follow_redirects=True
        ) as client:
            response = await client.get(url)
            if response.status_code != 200:
                return []
            return self._parse_iah_html(response.text, ano_min)

    def _parse_bvs_html(self, html: str, ano_min: int) -> List[Dict[str, Any]]:
        """Parse do HTML do portal BVS"""
        resultados = []
        soup = BeautifulSoup(html, 'lxml')

        # O portal BVS usa estrutura similar ao search.scielo.org
        itens = (
            soup.select('.resultados .resultado')
            or soup.select('.result-item')
            or soup.select('li.item')
            or soup.select('.artigo, article')
        )

        for item in itens:
            try:
                resultado = self._parse_bvs_item(item, ano_min)
                if resultado:
                    resultados.append(resultado)
            except Exception:
                continue

        return resultados[:20]

    def _parse_bvs_item(self, item, ano_min: int) -> Optional[Dict[str, Any]]:
        """Parse de um item de resultado do BVS"""
        titulo_el = (
            item.select_one('.article-title a')
            or item.select_one('h4 a')
            or item.select_one('h3 a')
            or item.select_one('.title a')
            or item.select_one('a.title')
        )
        if not titulo_el:
            return None

        titulo = titulo_el.get_text(strip=True)
        if not titulo or len(titulo) < 5:
            return None

        link = titulo_el.get('href', '') or ''
        if link and not link.startswith('http'):
            link = f"https://pesquisa.bvsalud.org{link}"

        autores = []
        autores_el = item.select_one('.authors, .line-authors, .author')
        if autores_el:
            texto = autores_el.get_text(separator=';', strip=True)
            autores = [a.strip() for a in re.split(r'[;,]', texto) if a.strip()][:10]

        resumo_el = item.select_one('.abstract, .resumo, .description')
        resumo = resumo_el.get_text(strip=True)[:2000] if resumo_el else None

        ano = self._extrair_ano(str(item))
        if ano and ano < ano_min:
            return None

        doi = self._extrair_doi(str(item))

        return {
            "titulo": titulo,
            "autores": autores if autores else None,
            "resumo": resumo,
            "url": link or None,
            "fonte": "LILACS",
            "tipo": "artigo",
            "ano": ano or datetime.now().year,
            "doi": doi,
            "keywords": [],
        }

    def _parse_iah_html(self, html: str, ano_min: int) -> List[Dict[str, Any]]:
        """Parse do HTML da interface iAHx da BIREME"""
        resultados = []
        soup = BeautifulSoup(html, 'lxml')

        # A interface iAHx usa tabelas ou divs com classe específica
        itens = (
            soup.select('.doc-resume')
            or soup.select('tr.resultado')
            or soup.select('.resultados tr')
            or soup.select('.resultado')
        )

        for item in itens:
            try:
                titulo_el = item.select_one('.doc-title, h4, td a')
                if not titulo_el:
                    continue

                titulo = titulo_el.get_text(strip=True)
                if not titulo or len(titulo) < 5:
                    continue

                link = titulo_el.get('href', '') or ''

                autores = []
                autor_el = item.select_one('.author, .doc-author, td:nth-child(2)')
                if autor_el:
                    texto = autor_el.get_text(strip=True)
                    autores = [a.strip() for a in re.split(r'[;,]', texto) if a.strip()][:10]

                resumo_el = item.select_one('.doc-resume, .abstract')
                resumo = resumo_el.get_text(strip=True)[:2000] if resumo_el else None

                ano = self._extrair_ano(str(item))
                if ano and ano < ano_min:
                    continue

                doi = self._extrair_doi(str(item))

                resultados.append({
                    "titulo": titulo,
                    "autores": autores if autores else None,
                    "resumo": resumo,
                    "url": link or None,
                    "fonte": "LILACS",
                    "tipo": "artigo",
                    "ano": ano or datetime.now().year,
                    "doi": doi,
                    "keywords": [],
                })
            except Exception:
                continue

        return resultados[:20]

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

    async def buscar_tese_dissertacao(self, termo: str) -> List[Dict[str, Any]]:
        """Busca teses e dissertações sobre o termo"""
        return await self.buscar(f"{termo} tese dissertação", 2016)
