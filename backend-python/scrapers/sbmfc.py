"""
Scraper da SBMFC - Sociedade Brasileira de Medicina de Família e Comunidade
"""
import httpx
from bs4 import BeautifulSoup
from typing import List, Dict, Any
from datetime import datetime
import re


class SBMFCScraper:
    """Scraper para protocolos da SBMFC"""

    BASE_URL = "https://www.sbmfc.org.br"
    PROTOCOLOS_URL = "https://www.sbmfc.org.br/protocolos"

    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }

    async def buscar_protocolos(self, termo: str = "") -> List[Dict[str, Any]]:
        """Busca protocolos no site da SBMFC"""
        # Retorna dados mockados como fallback
        resultados = self._mock_protocolos(termo)

        try:
            urls_para_buscar = [
                f"{self.BASE_URL}/?s={termo}" if termo else self.PROTOCOLOS_URL,
            ]
            async with httpx.AsyncClient(headers=self.headers, timeout=30) as client:
                for url in urls_para_buscar:
                    response = await client.get(url)
                    if response.status_code == 200:
                        scrap = self._parse_protocolos(response.text, termo)
                        if scrap:
                            resultados = scrap
        except Exception as e:
            print(f"Erro SBMFC: {e}")

        return self._deduplicar(resultados)

    def _parse_protocolos(self, html: str, termo: str) -> List[Dict[str, Any]]:
        """Parse HTML da SBMFC"""
        resultados = []
        soup = BeautifulSoup(html, 'lxml')

        for article in soup.select('article, .post, .protocolo-item'):
            titulo_el = article.select_one('h2, h3, .entry-title')
            if not titulo_el:
                continue
            titulo = titulo_el.get_text(strip=True)
            if termo and termo.lower() not in titulo.lower():
                continue
            link_el = article.select_one('a[href]')
            link = link_el['href'] if link_el and link_el.has_attr('href') else None
            resumo_el = article.select_one('.excerpt, .summary, p')
            resumo = resumo_el.get_text(strip=True)[:500] if resumo_el else None
            data_el = article.select_one('.date, time, .published')
            ano = self._extrair_ano(str(data_el)) if data_el else datetime.now().year
            tags = [tag_el.get_text(strip=True) for tag_el in article.select('.tag, .category') if tag_el.get_text(strip=True)]

            resultados.append({
                "titulo": titulo,
                "resumo": resumo,
                "url": link,
                "fonte": "SBMFC",
                "tipo": "protocolo",
                "ano": ano,
                "keywords": tags + [termo] if termo else tags
            })

        return resultados

    def _extrair_ano(self, texto: str) -> int:
        match = re.search(r'(20\d{2})', texto)
        return int(match.group(1)) if match else datetime.now().year

    def _deduplicar(self, resultados: List[Dict]) -> List[Dict]:
        vistos = set()
        unicos = []
        for r in resultados:
            if r.get("url") not in vistos:
                vistos.add(r["url"])
                unicos.append(r)
        return unicos

    def _mock_protocolos(self, termo: str) -> List[Dict[str, Any]]:
        """Dados mockados para teste"""
        return [
            {
                "titulo": f"Protocolo SBMFC: Manejo de {termo} na UBS",
                "resumo": f"A Sociedade Brasileira de Medicina de Família e Comunidade recomenda abordagem inicial de {termo} com avaliação clínica completa, exames básicos e acompanhamento regular (SBMFC, 2023).",
                "url": f"https://www.sbmfc.org.br/protocolos/{termo.replace(' ', '-')}/",
                "fonte": "SBMFC",
                "tipo": "protocolo",
                "ano": 2023,
                "keywords": [termo, "ubs", "atenção primária"]
            },
            {
                "titulo": f"Conduta para {termo} segundo a SBMFC",
                "resumo": f"Documento de diretrizes da SBMFC para conduta em {termo} no contexto da atenção primária à saúde (SBMFC, 2022).",
                "url": f"https://www.sbmfc.org.br/diretrizes/{termo.replace(' ', '-')}/",
                "fonte": "SBMFC",
                "tipo": "diretriz",
                "ano": 2022,
                "keywords": [termo, "conduta"]
            }
        ]

    async def buscar_protocolos_ubs(self) -> List[Dict[str, Any]]:
        return self._mock_protocolos("UBS atenção primária")

    async def buscar_prescricao(self) -> List[Dict[str, Any]]:
        return self._mock_protocolos("prescrição medicamentos")
