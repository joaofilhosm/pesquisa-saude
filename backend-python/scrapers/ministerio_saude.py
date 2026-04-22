"""
Scraper do Ministério da Saúde - PCDT e BVS

Busca Protocolos Clínicos e Diretrizes Terapêuticas (PCDT) no gov.br
e documentos técnicos na Biblioteca Virtual em Saúde (BVS/MS).
Nenhum dado é fabricado: se a busca falha, retorna lista vazia.
"""
import httpx
from bs4 import BeautifulSoup
from typing import List, Dict, Optional, Any
import re
import urllib.parse
from datetime import datetime

from .cache import cache_medio, cache_longo


class MinisterioSaudeScraper:
    """Scraper para Protocolos Clínicos e Diretrizes Terapêuticas (PCDT)"""

    # Página com todos os PCDTs publicados
    PCDT_LIST_URL = "https://www.gov.br/saude/pt-br/composicao/sctie/protocolos-e-diretrizes-terapeuticas-pcdt"
    # Busca geral no MS
    MS_SEARCH_URL = "https://www.gov.br/saude/pt-br/search"
    # BVS do Ministério da Saúde
    BVS_URL = "https://bvsms.saude.gov.br"

    # Palavras-chave que identificam documentos do tipo PCDT/protocolo
    PCDT_KEYWORDS = frozenset(['protocolo', 'diretriz', 'pcdt', 'terapêutica', 'terapeutica'])

    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "pt-BR,pt;q=0.9",
        }

    async def buscar_pcdt(self, termo: str) -> List[Dict[str, Any]]:
        """Busca PCDT por termo no gov.br"""
        cache_key = f"pcdt_{termo}"
        cached = cache_medio.get(cache_key)
        if cached is not None:
            return cached

        resultados = []

        # Tentar busca geral no site do Ministério
        try:
            resultados = await self._buscar_ms_search(termo)
        except Exception as e:
            print(f"Erro MS search: {e}")

        # Tentar listar PCDTs e filtrar pelo termo
        if not resultados:
            try:
                todos_pcdt = await self._listar_todos_pcdt()
                resultados = [
                    p for p in todos_pcdt
                    if termo.lower() in p.get("titulo", "").lower()
                ][:10]
            except Exception as e:
                print(f"Erro listagem PCDT: {e}")

        cache_medio.set(cache_key, resultados)
        return resultados

    async def _buscar_ms_search(self, termo: str) -> List[Dict[str, Any]]:
        """Busca no site do Ministério da Saúde usando o mecanismo de busca"""
        query = urllib.parse.quote(f"{termo} protocolo diretriz")
        url = f"{self.MS_SEARCH_URL}?SearchableText={query}"

        async with httpx.AsyncClient(
            headers=self.headers, timeout=30, follow_redirects=True
        ) as client:
            response = await client.get(url)
            if response.status_code != 200:
                return []
            return self._parse_ms_resultados(response.text, termo)

    async def _listar_todos_pcdt(self) -> List[Dict[str, Any]]:
        """Lista todos os PCDTs da página do Ministério"""
        cache_key = "pcdt_todos"
        cached = cache_longo.get(cache_key)
        if cached is not None:
            return cached

        async with httpx.AsyncClient(
            headers=self.headers, timeout=30, follow_redirects=True
        ) as client:
            response = await client.get(self.PCDT_LIST_URL)
            if response.status_code != 200:
                return []

        resultados = self._parse_pcdt_lista(response.text)
        cache_longo.set(cache_key, resultados)
        return resultados

    def _parse_ms_resultados(self, html: str, termo: str) -> List[Dict[str, Any]]:
        """Parse dos resultados da busca no site do MS"""
        resultados = []
        soup = BeautifulSoup(html, 'lxml')

        # O Plone (CMS do gov.br) tem estrutura específica
        itens = (
            soup.select('.searchResults .searchResult')
            or soup.select('.search-result, .result-item')
            or soup.select('article')
            or soup.select('.listing-item')
        )

        for item in itens:
            titulo_el = (
                item.select_one('h3 a, h4 a, .tileHeadline a, .documentFirstHeading a')
                or item.select_one('a[href*="saude"]')
                or item.select_one('a')
            )
            if not titulo_el:
                continue

            titulo = titulo_el.get_text(strip=True)
            if not titulo or len(titulo) < 5:
                continue

            link = titulo_el.get('href', '') or ''
            if link and not link.startswith('http'):
                link = f"https://www.gov.br{link}"

            resumo_el = item.select_one('.tileBody, .description, p, .summary')
            resumo = resumo_el.get_text(strip=True)[:1000] if resumo_el else None

            ano = self._extrair_ano(str(item))

            resultados.append({
                "titulo": titulo,
                "resumo": resumo,
                "url": link or None,
                "fonte": "Ministério da Saúde",
                "tipo": "pcdt",
                "ano": ano,
                "keywords": [termo, "pcdt", "protocolo"],
            })

        return resultados[:20]

    def _parse_pcdt_lista(self, html: str) -> List[Dict[str, Any]]:
        """Parse da página de lista de todos os PCDTs"""
        resultados = []
        soup = BeautifulSoup(html, 'lxml')

        # Buscar links que parecem ser PCDTs
        for link_el in soup.select('a[href]'):
            href = link_el.get('href', '')
            titulo = link_el.get_text(strip=True)

            if not titulo or len(titulo) < 10:
                continue

            # Filtrar apenas links que parecem ser documentos/PDFs de PCDT
            if not any(k in titulo.lower() for k in self.PCDT_KEYWORDS):
                continue

            if href and not href.startswith('http'):
                href = f"https://www.gov.br{href}"

            ano = self._extrair_ano(titulo + href)

            resultados.append({
                "titulo": titulo,
                "resumo": None,
                "url": href or None,
                "fonte": "Ministério da Saúde",
                "tipo": "pcdt",
                "ano": ano,
                "keywords": ["pcdt", "protocolo"],
            })

        return resultados[:50]  # Guardar no cache para filtrar depois

    async def buscar_bvs(self, termo: str) -> List[Dict[str, Any]]:
        """Busca na Biblioteca Virtual em Saúde do Ministério"""
        cache_key = f"bvs_ms_{termo}"
        cached = cache_medio.get(cache_key)
        if cached is not None:
            return cached

        resultados = []
        try:
            query = urllib.parse.quote(termo)
            url = f"{self.BVS_URL}/bvs/publicacoes/search?q={query}"

            async with httpx.AsyncClient(
                headers=self.headers, timeout=30, follow_redirects=True
            ) as client:
                response = await client.get(url)
                if response.status_code == 200:
                    resultados = self._parse_bvs_resultados(response.text, termo)
        except Exception as e:
            print(f"Erro BVS/MS: {e}")

        cache_medio.set(cache_key, resultados)
        return resultados

    def _parse_bvs_resultados(self, html: str, termo: str) -> List[Dict[str, Any]]:
        """Parse dos resultados da BVS do Ministério"""
        resultados = []
        soup = BeautifulSoup(html, 'lxml')

        for item in soup.select('.resultado, .result, article, .publicacao-item'):
            titulo_el = item.select_one('h4 a, h3 a, h2 a, .title a, a.titulo')
            if not titulo_el:
                continue

            titulo = titulo_el.get_text(strip=True)
            if not titulo or len(titulo) < 5:
                continue

            link = titulo_el.get('href', '') or ''
            if link and not link.startswith('http'):
                link = f"{self.BVS_URL}{link}"

            resumo_el = item.select_one('.description, .resumo, p')
            resumo = resumo_el.get_text(strip=True)[:1000] if resumo_el else None

            ano = self._extrair_ano(str(item))

            resultados.append({
                "titulo": titulo,
                "resumo": resumo,
                "url": link or None,
                "fonte": "BVS/MS",
                "tipo": "protocolo",
                "ano": ano,
                "keywords": [termo],
            })

        return resultados[:20]

    def _extrair_ano(self, texto: str) -> Optional[int]:
        """Extrai ano de um texto"""
        anos = re.findall(r'(20\d{2})', texto)
        if not anos:
            return None
        anos_validos = [int(a) for a in anos if 2000 <= int(a) <= datetime.now().year]
        return max(anos_validos) if anos_validos else None

    async def buscar_protocolos_urgencia(self) -> List[Dict[str, Any]]:
        """Busca protocolos de urgência e emergência"""
        return await self.buscar_pcdt("urgência emergência")

    async def buscar_protocolos_ubs(self) -> List[Dict[str, Any]]:
        """Busca protocolos para UBS/Atenção Primária"""
        return await self.buscar_pcdt("atenção primária")

    async def buscar_medicamentos(self, medicamento: str) -> List[Dict[str, Any]]:
        """Busca protocolos específicos de medicamentos"""
        return await self.buscar_pcdt(medicamento)
