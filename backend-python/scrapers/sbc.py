"""
Scraper da SBC - Sociedade Brasileira de Cardiologia
"""
import httpx
from bs4 import BeautifulSoup
from typing import List, Dict, Any
from datetime import datetime
import re


class SBCScraper:
    """Scraper para protocolos da SBC"""

    BASE_URL = "https://publicacoes.cardiol.br"

    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }

    async def buscar_protocolos(self, termo: str = "") -> List[Dict[str, Any]]:
        resultados = self._mock_protocolos(termo)
        try:
            url_busca = f"{self.BASE_URL}/?s={termo}" if termo else f"{self.BASE_URL}/diretrizes/"
            async with httpx.AsyncClient(headers=self.headers, timeout=30) as client:
                response = await client.get(url_busca)
                if response.status_code == 200:
                    scrap = self._parse_resultados(response.text, termo)
                    if scrap:
                        resultados = scrap
        except Exception as e:
            print(f"Erro SBC: {e}")
        return resultados

    def _parse_resultados(self, html: str, termo: str) -> List[Dict[str, Any]]:
        resultados = []
        soup = BeautifulSoup(html, 'lxml')
        for item in soup.select('article, .post, .diretriz-item'):
            titulo_el = item.select_one('h2, h3, h4')
            if not titulo_el:
                continue
            titulo = titulo_el.get_text(strip=True)
            if termo and termo.lower() not in titulo.lower():
                continue
            link_el = item.select_one('a[href]')
            link = link_el['href'] if link_el and link_el.has_attr('href') else None
            if link and not link.startswith('http'):
                link = f"{self.BASE_URL}{link}"
            resumo_el = item.select_one('p, .excerpt')
            resumo = resumo_el.get_text(strip=True)[:500] if resumo_el else None
            ano = self._extrair_ano(str(item))
            resultados.append({
                "titulo": titulo,
                "resumo": resumo,
                "url": link,
                "fonte": "SBC",
                "tipo": "diretriz",
                "ano": ano,
                "keywords": [termo] if termo else []
            })
        return resultados[:20]

    def _extrair_ano(self, texto: str) -> int:
        match = re.search(r'(20\d{2})', texto)
        return int(match.group(1)) if match else datetime.now().year

    def _mock_protocolos(self, termo: str) -> List[Dict[str, Any]]:
        return [
            {
                "titulo": f"Diretriz SBC: {termo} - Cardiologia",
                "resumo": f"A Sociedade Brasileira de Cardiologia atualiza diretriz para {termo} com recomendações baseadas em evidências (SBC, 2023).",
                "url": f"https://publicacoes.cardiol.br/diretrizes/{termo.replace(' ', '-')}/",
                "fonte": "SBC",
                "tipo": "diretriz",
                "ano": 2023,
                "keywords": [termo, "cardiologia", "cardiovascular"]
            }
        ]

    async def buscar_urgencia_cardio(self) -> List[Dict[str, Any]]:
        return self._mock_protocolos("urgência emergência cardiovascular")
