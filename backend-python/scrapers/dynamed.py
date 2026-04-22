"""
Scraper do DynaMed - Ferramenta de Suporte à Decisão Clínica (EBSCO Health)

Usa a MedsAPI DynaMed v1 (EBSCO) para buscar monografias clínicas:
tópicos de condições médicas, fármacos e diretrizes baseadas em evidências.

Autenticação: OAuth 2.0 Client Credentials (EBSCO Developer Portal).
  DYNAMED_CLIENT_ID    — client_id obtido no portal EBSCO
  DYNAMED_CLIENT_SECRET — client_secret correspondente

Sem as credenciais configuradas, o scraper retorna lista vazia sem erros.
Obtenha acesso de desenvolvedor em: https://developer.ebsco.com/

Referências:
  - https://developer.ebsco.com/medical-point-care-apis/dynamed/docs/search-get
  - https://apis.ebsco.com/medsapi-dynamed/v1/search
"""
import httpx
import os
import time
from typing import List, Dict, Any, Optional

from .cache import cache_medio


class DynaMedScraper:
    """
    Scraper para DynaMed via EBSCO MedsAPI.

    DynaMed é uma das principais ferramentas de suporte à decisão clínica,
    com monografias baseadas em evidências para condições, fármacos e testes.
    Diferente de bases de artigos (PubMed/SciELO), retorna tópicos clínicos
    estruturados com resumo, tipo de publicação e link direto à monografia.

    Requer DYNAMED_CLIENT_ID e DYNAMED_CLIENT_SECRET no .env —
    registre sua aplicação em https://developer.ebsco.com/
    """

    TOKEN_URL = "https://apis.ebsco.com/medsapi-dynamed/v1/auth/token"
    SEARCH_URL = "https://apis.ebsco.com/medsapi-dynamed/v1/search"
    ARTICLE_BASE = "https://www.dynamed.com"

    def __init__(self):
        self.client_id = os.getenv("DYNAMED_CLIENT_ID")
        self.client_secret = os.getenv("DYNAMED_CLIENT_SECRET")
        self.headers = {
            "User-Agent": "PesquisaSaude/3.0 (https://github.com/joaofilhosm/pesquisa-saude)",
            "Accept": "application/json",
        }
        # Cache de token em memória: (access_token, expires_at)
        self._token: Optional[str] = None
        self._token_expires_at: float = 0.0

    async def _get_token(self) -> Optional[str]:
        """Obtém (ou reutiliza) o token OAuth 2.0 via client credentials."""
        if self._token and time.time() < self._token_expires_at - 30:
            return self._token

        try:
            async with httpx.AsyncClient(timeout=20) as client:
                response = await client.post(
                    self.TOKEN_URL,
                    data={
                        "grant_type": "client_credentials",
                        "client_id": self.client_id,
                        "client_secret": self.client_secret,
                    },
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                )
                if response.status_code == 200:
                    data = response.json()
                    self._token = data.get("access_token")
                    expires_in = data.get("expires_in", 3600)
                    self._token_expires_at = time.time() + float(expires_in)
                    return self._token
                else:
                    print(f"DynaMed: falha ao obter token (status {response.status_code})")
                    return None
        except Exception as e:
            print(f"DynaMed: erro ao obter token OAuth: {e}")
            return None

    async def buscar(self, termo: str, ano_min: int = 2016) -> List[Dict[str, Any]]:
        """
        Busca tópicos clínicos no DynaMed via EBSCO MedsAPI.

        Retorna lista vazia se as credenciais não estiverem configuradas
        ou se a busca falhar (sem dados fictícios).

        Nota: DynaMed retorna monografias clínicas (condições, fármacos),
        não artigos individuais — `ano_min` não é aplicável mas mantido
        para uniformidade com as demais fontes.
        """
        if not self.client_id or not self.client_secret:
            return []

        cache_key = f"dynamed_{termo}_{ano_min}"
        cached = cache_medio.get(cache_key)
        if cached is not None:
            return cached

        resultados: List[Dict[str, Any]] = []
        try:
            token = await self._get_token()
            if not token:
                return []

            auth_headers = {**self.headers, "Authorization": f"Bearer {token}"}
            params = {
                "query": termo,
                "pubTypeId": ["condition", "drug"],
            }

            async with httpx.AsyncClient(headers=auth_headers, timeout=30) as client:
                response = await client.get(self.SEARCH_URL, params=params)
                if response.status_code == 200:
                    resultados = self._parse_resultados(response.json(), termo)
                elif response.status_code == 401:
                    # Token pode ter expirado antes da margem de 30s; tentar renovar
                    self._token = None
                    token = await self._get_token()
                    if token:
                        auth_headers["Authorization"] = f"Bearer {token}"
                        r2 = await client.get(self.SEARCH_URL, params=params,
                                              headers=auth_headers)
                        if r2.status_code == 200:
                            resultados = self._parse_resultados(r2.json(), termo)
                        else:
                            print(f"DynaMed: status {r2.status_code} após retry")
                    else:
                        print("DynaMed: credenciais inválidas.")
                elif response.status_code == 429:
                    print("DynaMed: rate limit atingido.")
                else:
                    print(f"DynaMed: status {response.status_code}")

        except Exception as e:
            print(f"Erro DynaMed: {e}")

        cache_medio.set(cache_key, resultados)
        return resultados

    def _parse_resultados(self, data: Dict, termo: str) -> List[Dict[str, Any]]:
        """Converte a resposta JSON do DynaMed para o formato padrão."""
        resultados = []
        items = data.get("items") or []

        for item in items[:20]:
            try:
                titulo = (item.get("title") or "").strip()
                if not titulo or len(titulo) < 3:
                    continue

                # Resumo / descrição da monografia
                resumo: Optional[str] = (item.get("description") or "").strip() or None
                if resumo and len(resumo) > 3000:
                    resumo = resumo[:3000]

                # URL da monografia no site DynaMed
                slug = item.get("slug") or ""
                url: Optional[str] = f"{self.ARTICLE_BASE}{slug}" if slug else None

                # Se não houver slug, tentar via links
                if not url:
                    links = item.get("links") or []
                    for lnk in links:
                        if lnk.get("rel") == "self":
                            url = lnk.get("href")
                            break

                # Tipo de publicação (Condition, Drug, etc.)
                pub_type = (
                    (item.get("pubType") or {}).get("title") or "Condition"
                ).strip()
                # Mapear para tipo padronizado do projeto
                tipo_map = {
                    "Condition": "diretriz",
                    "Drug": "diretriz",
                    "Image": None,   # ignorar imagens
                }
                tipo = tipo_map.get(pub_type, "diretriz")
                if tipo is None:
                    continue

                resultados.append({
                    "titulo": titulo,
                    "autores": None,     # monografias DynaMed não têm autor individual
                    "resumo": resumo,
                    "url": url,
                    "fonte": "DynaMed",
                    "journal": "DynaMed (EBSCO Health)",
                    "volume": "",
                    "issue": "",
                    "paginas": "",
                    "tipo": tipo,
                    "ano": None,         # monografias são atualizadas continuamente
                    "doi": None,
                    "pmid": None,
                    "keywords": [termo, pub_type.lower()],
                })
            except Exception:
                continue

        return resultados
