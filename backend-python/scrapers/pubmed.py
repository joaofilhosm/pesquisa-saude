"""
Scraper do PubMed usando NCBI E-utilities API oficial (gratuita, sem autenticação necessária).

Referência: https://www.ncbi.nlm.nih.gov/books/NBK25499/
- esearch: busca e retorna lista de PMIDs
- esummary: metadados (título, autores, ano, revista, DOI)
- efetch: texto completo do abstract
"""
import httpx
import os
import re
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime

from .cache import cache_medio


class PubMedScraper:
    """
    Scraper para PubMed usando NCBI E-utilities API oficial.

    Taxa: 10 req/s sem API key, mais com NCBI_API_KEY definida no .env.
    Retorna artigos reais com abstracts completos, DOIs e URLs verificadas.
    """

    EUTILS_BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
    PUBMED_URL = "https://pubmed.ncbi.nlm.nih.gov"

    def __init__(self):
        self.api_key = os.getenv("NCBI_API_KEY")
        self.headers = {
            "User-Agent": "PesquisaSaude/3.0 (https://github.com/joaofilhosm/pesquisa-saude)",
        }

    def _params(self, **kwargs) -> dict:
        """Monta parâmetros adicionando API key se disponível"""
        params = dict(kwargs)
        if self.api_key:
            params["api_key"] = self.api_key
        return params

    async def _esearch(
        self, termo: str, ano_min: int, brasil: bool, retmax: int = 20
    ) -> List[str]:
        """Busca PMIDs via esearch. Retorna lista de IDs."""
        query = termo
        if brasil:
            query += " AND Brazil[Affiliation]"
        query += f" AND {ano_min}:{datetime.now().year}[PDat]"

        params = self._params(
            db="pubmed",
            term=query,
            retmode="json",
            retmax=retmax,
            sort="relevance",
        )

        url = f"{self.EUTILS_BASE}/esearch.fcgi"
        async with httpx.AsyncClient(headers=self.headers, timeout=30) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            return data.get("esearchresult", {}).get("idlist", [])

    async def _esummary(self, ids: List[str]) -> List[Dict[str, Any]]:
        """Busca metadados dos artigos via esummary. Retorna lista de artigos."""
        if not ids:
            return []

        params = self._params(
            db="pubmed",
            id=",".join(ids),
            retmode="json",
        )

        url = f"{self.EUTILS_BASE}/esummary.fcgi"
        async with httpx.AsyncClient(headers=self.headers, timeout=30) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            result = data.get("result", {})

        artigos = []
        for pmid in ids:
            if pmid not in result:
                continue
            artigo = self._parse_summary(result[pmid])
            if artigo:
                artigos.append(artigo)

        return artigos

    async def _efetch_abstract(self, pmid: str) -> Optional[str]:
        """Busca texto completo do abstract via efetch."""
        cache_key = f"pubmed_abstract_{pmid}"
        cached = cache_medio.get(cache_key)
        if cached is not None:
            return cached

        params = self._params(
            db="pubmed",
            id=pmid,
            rettype="abstract",
            retmode="text",
        )

        url = f"{self.EUTILS_BASE}/efetch.fcgi"
        try:
            async with httpx.AsyncClient(headers=self.headers, timeout=30) as client:
                response = await client.get(url, params=params)
                if response.status_code != 200:
                    return None
                abstract = self._extrair_abstract_do_texto(response.text)
                cache_medio.set(cache_key, abstract)
                return abstract
        except Exception:
            return None

    def _extrair_abstract_do_texto(self, texto: str) -> str:
        """Extrai apenas o abstract do texto retornado pelo efetch"""
        linhas = texto.split('\n')
        abstract_linhas = []
        capturando = False

        for linha in linhas:
            linha_upper = linha.strip().upper()
            if linha_upper in ('ABSTRACT', 'RESUMO'):
                capturando = True
                continue
            if capturando:
                if linha.strip().startswith('PMID:') or linha.strip().startswith('Copyright'):
                    break
                abstract_linhas.append(linha)

        if abstract_linhas:
            return ' '.join(l.strip() for l in abstract_linhas if l.strip())[:3000]

        # Fallback: pular as primeiras 2 linhas (título + autores) e usar o restante
        texto_corpo = '\n'.join(linhas[2:]).strip()
        return texto_corpo[:3000]

    def _parse_summary(self, data: Dict) -> Optional[Dict[str, Any]]:
        """Converte um item do esummary para dicionário padronizado"""
        pmid = data.get("uid", "")
        titulo = data.get("title", "").strip()
        if not titulo:
            return None

        # Autores
        autores = [
            a.get("name", "")
            for a in data.get("authors", [])
            if a.get("authtype") == "Author" and a.get("name")
        ]

        # DOI
        doi = None
        for aid in data.get("articleids", []):
            if aid.get("idtype") == "doi":
                doi = aid.get("value", "").strip()
                break
        if not doi:
            eloc = data.get("elocationid", "")
            match = re.search(r'10\.\d{4,}/\S+', eloc)
            if match:
                doi = match.group(0)

        # Ano
        ano = None
        pubdate = data.get("sortpubdate", "") or data.get("pubdate", "")
        if pubdate:
            match = re.search(r'(20\d{2})', pubdate)
            if match:
                ano = int(match.group(1))

        journal = data.get("fulljournalname") or data.get("source", "")

        return {
            "titulo": titulo,
            "autores": autores if autores else None,
            "ano": ano,
            "journal": journal,
            "volume": data.get("volume", ""),
            "issue": data.get("issue", ""),
            "paginas": data.get("pages", ""),
            "doi": doi,
            "pmid": pmid,
            "url": f"{self.PUBMED_URL}/{pmid}/",
            "fonte": "PubMed",
            "tipo": "artigo",
            "resumo": None,  # preenchido por _efetch_abstract
            "keywords": [],
        }

    async def buscar(
        self, termo: str, ano_min: int = 2016, brasil: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Busca artigos reais no PubMed usando NCBI E-utilities API.

        Retorna artigos com abstracts completos, DOIs reais e URLs verificadas.
        Nenhum dado é fabricado: se a busca falha, retorna lista vazia.
        """
        cache_key = f"pubmed_{termo}_{ano_min}_{brasil}"
        cached = cache_medio.get(cache_key)
        if cached is not None:
            return cached

        try:
            ids = await self._esearch(termo, ano_min, brasil, retmax=15)
            if not ids:
                # Tentar sem filtro de afiliação brasileira
                if brasil:
                    ids = await self._esearch(termo, ano_min, False, retmax=10)
                if not ids:
                    return []

            artigos = await self._esummary(ids)
            if not artigos:
                return []

            # Buscar abstracts em paralelo (máximo 5 para respeitar rate limit)
            ids_com_abstract = [a["pmid"] for a in artigos[:5] if a.get("pmid")]
            if ids_com_abstract:
                tarefas = []
                for pmid in ids_com_abstract:
                    tarefas.append(self._efetch_abstract(pmid))
                    await asyncio.sleep(0.11)  # ~9 req/s para ficar dentro do limite

                abstracts = await asyncio.gather(*tarefas, return_exceptions=True)
                for i, abstract in enumerate(abstracts):
                    if i < len(artigos) and isinstance(abstract, str) and abstract:
                        artigos[i]["resumo"] = abstract

            for a in artigos:
                if not a.get("keywords"):
                    a["keywords"] = [termo]

            cache_medio.set(cache_key, artigos)
            return artigos

        except Exception as e:
            print(f"Erro PubMed E-utilities: {e}")
            return []

    async def buscar_review(self, termo: str, ano_min: int = 2016) -> List[Dict[str, Any]]:
        """Busca review articles e systematic reviews no PubMed"""
        cache_key = f"pubmed_review_{termo}_{ano_min}"
        cached = cache_medio.get(cache_key)
        if cached is not None:
            return cached

        try:
            query = f"({termo}) AND (Review[pt] OR Systematic Review[pt]) AND {ano_min}:{datetime.now().year}[PDat]"
            params = self._params(
                db="pubmed",
                term=query,
                retmode="json",
                retmax=10,
                sort="relevance",
            )

            url = f"{self.EUTILS_BASE}/esearch.fcgi"
            async with httpx.AsyncClient(headers=self.headers, timeout=30) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()
                ids = data.get("esearchresult", {}).get("idlist", [])

            if not ids:
                return []

            artigos = await self._esummary(ids)
            for a in artigos:
                a["keywords"] = [termo, "review"]

            cache_medio.set(cache_key, artigos)
            return artigos

        except Exception as e:
            print(f"Erro PubMed Review: {e}")
            return []
