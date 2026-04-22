"""
Scraper da SciELO - Scientific Electronic Library Online

Usa o endpoint de busca do search.scielo.org com parsing HTML real.
Nenhum dado é fabricado: se a busca falha, retorna lista vazia.
"""
import httpx
from bs4 import BeautifulSoup
from typing import List, Dict, Any, Optional
from datetime import datetime
import re
import urllib.parse

from .cache import cache_medio


class SciELOScraper:
    """Scraper para base SciELO via search.scielo.org"""

    SEARCH_URL = "https://search.scielo.org"
    SCIELO_BASE = "https://www.scielo.br"

    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
        }

    async def buscar(self, termo: str, ano_min: int = 2016) -> List[Dict[str, Any]]:
        """
        Busca artigos reais na SciELO.
        Retorna lista vazia se a busca falhar (sem dados fictícios).
        """
        cache_key = f"scielo_{termo}_{ano_min}"
        cached = cache_medio.get(cache_key)
        if cached is not None:
            return cached

        resultados = []
        try:
            query = urllib.parse.quote(termo)
            ano_atual = datetime.now().year
            url = (
                f"{self.SEARCH_URL}/?q={query}"
                f"&lang=pt&count=20&from={ano_min}&to={ano_atual}"
            )
            async with httpx.AsyncClient(
                headers=self.headers, timeout=30, follow_redirects=True
            ) as client:
                response = await client.get(url)
                if response.status_code == 200:
                    resultados = self._parse_resultados(response.text, termo, ano_min)
        except Exception as e:
            print(f"Erro SciELO (search.scielo.org): {e}")

        cache_medio.set(cache_key, resultados)
        return resultados

    def _parse_resultados(
        self, html: str, termo: str, ano_min: int
    ) -> List[Dict[str, Any]]:
        """Parse dos resultados da busca no search.scielo.org"""
        resultados = []
        soup = BeautifulSoup(html, 'lxml')

        # SciELO usa diferentes estruturas dependendo da versão
        # Tenta múltiplos seletores para cobrir variações
        itens = (
            soup.select('li.item')
            or soup.select('div.item')
            or soup.select('.resultados .resultado')
            or soup.select('article')
        )

        for item in itens:
            try:
                resultado = self._parse_item(item, ano_min)
                if resultado:
                    resultados.append(resultado)
            except Exception:
                continue

        # Remover duplicatas por URL
        vistos = set()
        unicos = []
        for r in resultados:
            chave = r.get("url") or r.get("doi") or r.get("titulo", "")[:80]
            if chave and chave not in vistos:
                vistos.add(chave)
                unicos.append(r)

        return unicos[:20]

    def _parse_item(self, item, ano_min: int) -> Optional[Dict[str, Any]]:
        """Parseia um item de resultado da SciELO"""
        # Título - múltiplos seletores
        titulo_el = (
            item.select_one('h4.article-title a')
            or item.select_one('.article-title a')
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

        # Link
        link = titulo_el.get('href', '')
        if link and not link.startswith('http'):
            link = f"{self.SCIELO_BASE}{link}"

        # Autores
        autores = []
        autores_el = (
            item.select_one('.authors')
            or item.select_one('.line-authors')
            or item.select_one('.author')
        )
        if autores_el:
            # Nomes separados por ';' ou em spans
            texto_autores = autores_el.get_text(separator=';', strip=True)
            autores = [a.strip() for a in re.split(r'[;,]', texto_autores) if a.strip()][:10]

        # Resumo
        resumo_el = (
            item.select_one('.abstract-content')
            or item.select_one('.article-abstract')
            or item.select_one('.abstract')
            or item.select_one('p.description')
        )
        resumo = resumo_el.get_text(strip=True)[:2000] if resumo_el else None

        # Ano e journal da linha de fonte
        fonte_el = (
            item.select_one('.line-source')
            or item.select_one('.source')
            or item.select_one('.journal-title')
        )
        ano = None
        journal = None
        volume = issue = paginas = ""
        if fonte_el:
            fonte_texto = fonte_el.get_text(strip=True)
            ano = self._extrair_ano(fonte_texto)
            journal = re.sub(r',.*', '', fonte_texto).strip()
            vol_match = re.search(r'v\.?\s*(\d+)', fonte_texto, re.IGNORECASE)
            if vol_match:
                volume = vol_match.group(1)
            num_match = re.search(r'n\.?\s*(\d+)', fonte_texto, re.IGNORECASE)
            if num_match:
                issue = num_match.group(1)
            pag_match = re.search(r'p\.?\s*([\d\-]+)', fonte_texto, re.IGNORECASE)
            if pag_match:
                paginas = pag_match.group(1)

        if not ano:
            ano = self._extrair_ano(str(item))
        if ano and ano < ano_min:
            return None

        # DOI
        doi = self._extrair_doi(str(item))
        if not doi and link:
            doi_match = re.search(r'10\.\d{4,}/\S+', link)
            if doi_match:
                doi = doi_match.group(0)

        # Keywords
        keywords = []
        kw_el = item.select('.keywords li, .keyword, [class*="keyword"]')
        for kw in kw_el:
            kw_text = kw.get_text(strip=True)
            if kw_text:
                keywords.append(kw_text)

        return {
            "titulo": titulo,
            "autores": autores if autores else None,
            "resumo": resumo,
            "url": link or None,
            "fonte": "SciELO",
            "journal": journal,
            "volume": volume,
            "issue": issue,
            "paginas": paginas,
            "tipo": "artigo",
            "ano": ano or datetime.now().year,
            "doi": doi,
            "keywords": keywords,
        }

    def _extrair_ano(self, texto: str) -> Optional[int]:
        """Extrai o ano mais recente válido do texto"""
        anos = re.findall(r'(20\d{2})', texto)
        if not anos:
            return None
        anos_validos = [int(a) for a in anos if 2000 <= int(a) <= datetime.now().year]
        return max(anos_validos) if anos_validos else None

    def _extrair_doi(self, texto: str) -> Optional[str]:
        """Extrai DOI do texto"""
        match = re.search(r'10\.\d{4,}/\S+', texto)
        if match:
            doi = match.group(0).rstrip('.,;)')
            return doi
        return None

    async def buscar_artigo_brasileiro(
        self, termo: str, area: str = "saude"
    ) -> List[Dict[str, Any]]:
        """Busca artigos brasileiros sobre o termo"""
        return await self.buscar(f"{termo} Brasil", ano_min=2016)
