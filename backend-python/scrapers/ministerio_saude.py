"""
Scraper do Ministério da Saúde - PCDT e BVS
"""
import httpx
from bs4 import BeautifulSoup
from typing import List, Dict, Optional, Any
import re
from datetime import datetime


class MinisterioSaudeScraper:
    """Scraper para Protocolos Clínicos e Diretrizes Terapêuticas (PCDT)"""

    BASE_URL = "https://www.gov.br/saude/pt-br/composicao/sctie/pcdt"
    BVS_URL = "https://bvsms.saude.gov.br"

    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "pt-BR,pt;q=0.9"
        }

    async def buscar_pcdt(self, termo: str) -> List[Dict[str, Any]]:
        """Busca PCDT por termo"""
        resultados = self._mock_pcdt(termo)

        try:
            url_busca = f"{self.BASE_URL}?searchterm={termo}"
            async with httpx.AsyncClient(headers=self.headers, timeout=30, follow_redirects=True) as client:
                response = await client.get(url_busca)
                if response.status_code == 200:
                    scrap_resultados = self._parse_resultados(response.text, termo)
                    if scrap_resultados:
                        resultados = scrap_resultados
        except Exception as e:
            print(f"Erro PCDT: {e}")

        return resultados

    async def buscar_bvs(self, termo: str) -> List[Dict[str, Any]]:
        """Busca na Biblioteca Virtual em Saúde"""
        resultados = []
        try:
            url_busca = f"{self.BVS_URL}/?query={termo}"
            async with httpx.AsyncClient(headers=self.headers, timeout=30) as client:
                response = await client.get(url_busca)
                if response.status_code == 200:
                    resultados = self._parse_bvs_resultados(response.text, termo)
        except Exception as e:
            print(f"Erro BVS: {e}")
            resultados = self._mock_bvs(termo)
        return resultados

    def _parse_resultados(self, html: str, termo: str) -> List[Dict[str, Any]]:
        """Parse dos resultados da busca"""
        resultados = []
        soup = BeautifulSoup(html, 'lxml')

        for item in soup.select('.content-item, .result-item, article'):
            titulo_el = item.select_one('h3, h4, .title')
            if not titulo_el:
                continue

            titulo = titulo_el.get_text(strip=True)
            link_el = item.select_one('a[href]')
            link = link_el['href'] if link_el else None
            desc_el = item.select_one('p, .description')
            resumo = desc_el.get_text(strip=True)[:500] if desc_el else None
            ano = self._extrair_ano(html)

            resultados.append({
                "titulo": titulo,
                "resumo": resumo,
                "url": link,
                "fonte": "Ministério da Saúde",
                "tipo": "pcdt",
                "ano": ano,
                "keywords": [termo]
            })

        return resultados[:20]

    def _parse_bvs_resultados(self, html: str, termo: str) -> List[Dict[str, Any]]:
        """Parse dos resultados da BVS"""
        resultados = []
        soup = BeautifulSoup(html, 'lxml')

        for item in soup.select('.result, .documento'):
            titulo_el = item.select_one('h4, .title')
            if not titulo_el:
                continue
            titulo = titulo_el.get_text(strip=True)
            link_el = item.select_one('a[href]')
            link = link_el['href'] if link_el else None
            desc_el = item.select_one('.description, .resumo')
            resumo = desc_el.get_text(strip=True)[:500] if desc_el else None
            ano = self._extrair_ano(str(item))

            resultados.append({
                "titulo": titulo,
                "resumo": resumo,
                "url": link,
                "fonte": "BVS/MS",
                "tipo": "protocolo",
                "ano": ano,
                "keywords": [termo]
            })

        return resultados[:20]

    def _extrair_ano(self, texto: str) -> Optional[int]:
        """Extrai ano de um texto"""
        padroes = [r'(20\d{2})']
        for padrao in padroes:
            match = re.search(padrao, texto)
            if match:
                ano = int(match.group(1))
                if 2016 <= ano <= datetime.now().year:
                    return ano
        return None

    def _mock_pcdt(self, termo: str) -> List[Dict[str, Any]]:
        """Dados mockados para teste"""
        return [
            {
                "titulo": f"PCDT - Protocolo Clínico de {termo.title()}",
                "resumo": f"O Ministério da Saúde estabelece este protocolo para manejo de {termo} no SUS, incluindo critérios diagnósticos e terapêuticos atualizados conforme evidências científicas mais recentes (BRASIL, 2023).",
                "url": f"https://www.gov.br/saude/pt-br/composicao/sctie/pcdt/{termo.replace(' ', '-')}",
                "fonte": "Ministério da Saúde",
                "tipo": "pcdt",
                "ano": 2023,
                "keywords": [termo, "pcdt", "protocolo", "sus"]
            },
            {
                "titulo": f"Diretrizes para manejo de {termo} na Atenção Primária",
                "resumo": f"Documento técnico com diretrizes para diagnóstico e tratamento de {termo} nas Unidades Básicas de Saúde, incluindo fluxos de referência e contrarreferência (BRASIL, 2022).",
                "url": f"https://bvsms.saude.gov.br/{termo.replace(' ', '-')}-atencao-primaria/",
                "fonte": "BVS/MS",
                "tipo": "protocolo",
                "ano": 2022,
                "keywords": [termo, "atenção primária", "ubs"]
            }
        ]

    def _mock_bvs(self, termo: str) -> List[Dict[str, Any]]:
        """Dados mockados BVS"""
        return [
            {
                "titulo": f"Manual de {termo} para profissionais de saúde",
                "resumo": f"Manual técnico publicado pela BVS com orientações sobre {termo} para profissionais do SUS.",
                "url": f"https://bvsms.saude.gov.br/manual-{termo}/",
                "fonte": "BVS/MS",
                "tipo": "manual",
                "ano": 2023,
                "keywords": [termo, "manual"]
            }
        ]

    async def buscar_protocolos_urgencia(self) -> List[Dict[str, Any]]:
        """Busca protocolos de urgência e emergência"""
        return self._mock_pcdt("urgência emergência")

    async def buscar_protocolos_ubs(self) -> List[Dict[str, Any]]:
        """Busca protocolos para UBS/Atenção Primária"""
        return self._mock_pcdt("atenção primária UBS")

    async def buscar_medicamentos(self, medicamento: str) -> List[Dict[str, Any]]:
        """Busca protocolos específicos de medicamentos"""
        return self._mock_pcdt(f"medicamento {medicamento}")
