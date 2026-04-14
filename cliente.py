"""
Cliente Python para API de Pesquisa em Saúde

Uso:
    from cliente import PesquisaSaudeClient

    client = PesquisaSaudeClient(
        api_key="sk-pesquisa-saude-2026-master-key",
        base_url="http://req.joaosmfilho.org"
    )

    resultados = client.pesquisar("diabetes")
    resposta = client.resposta("tratamento hipertensão")
"""

import httpx
from typing import Optional


class PesquisaSaudeClient:
    """Cliente para integrar a API de Pesquisa em Saúde em seus projetos."""

    def __init__(
        self,
        api_key: str = "sk-pesquisa-saude-2026-master-key",
        base_url: str = "http://req.joaosmfilho.org"
    ):
        self.api_key = api_key
        self.base_url = base_url
        self._headers = {"X-API-Key": self.api_key}

    def pesquisar(
        self,
        termo: str,
        fontes: Optional[list[str]] = None,
        ano_min: int = 2016,
        limit: int = 50
    ) -> dict:
        """
        Pesquisa em todas as fontes de saúde.

        Args:
            termo: Termo de busca (ex: "diabetes", "hipertensão")
            fontes: Lista de fontes específicas (opcional)
            ano_min: Ano mínimo dos resultados
            limit: Máximo de resultados

        Returns:
            Dict com 'resultados', 'total', 'query'
        """
        data = {
            "query": termo,
            "ano_min": ano_min,
            "limit": limit
        }
        if fontes:
            data["fontes"] = fontes

        with httpx.Client() as client:
            response = client.post(
                f"{self.base_url}/pesquisar",
                headers=self._headers,
                json=data
            )
            response.raise_for_status()
            return response.json()

    async def pesquisar_async(
        self,
        termo: str,
        fontes: Optional[list[str]] = None,
        ano_min: int = 2016,
        limit: int = 50
    ) -> dict:
        """Versão assíncrona do método pesquisar."""
        data = {
            "query": termo,
            "ano_min": ano_min,
            "limit": limit
        }
        if fontes:
            data["fontes"] = fontes

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/pesquisar",
                headers=self._headers,
                json=data
            )
            response.raise_for_status()
            return response.json()

    def resposta(self, query: str, ano_min: int = 2016) -> dict:
        """
        Gera resposta formatada com citações ABNT.

        Args:
            query: Termo ou pergunta (ex: "tratamento diabetes tipo 2")
            ano_min: Ano mínimo

        Returns:
            Dict com 'texto', 'citacoes_usadas', 'referencias'
        """
        with httpx.Client() as client:
            response = client.post(
                f"{self.base_url}/resposta",
                headers=self._headers,
                json={"query": query, "ano_min": ano_min}
            )
            response.raise_for_status()
            return response.json()

    async def resposta_async(self, query: str, ano_min: int = 2016) -> dict:
        """Versão assíncrona do método resposta."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/resposta",
                headers=self._headers,
                json={"query": query, "ano_min": ano_min}
            )
            response.raise_for_status()
            return response.json()

    def listar_fontes(self) -> dict:
        """Lista todas as fontes disponíveis."""
        with httpx.Client() as client:
            response = client.get(
                f"{self.base_url}/fontes",
                headers=self._headers
            )
            response.raise_for_status()
            return response.json()

    def info(self) -> dict:
        """Informações da API."""
        with httpx.Client() as client:
            response = client.get(f"{self.base_url}/")
            response.raise_for_status()
            return response.json()


# Exemplo de uso
if __name__ == "__main__":
    client = PesquisaSaudeClient()

    print("=== Testando API ===\n")

    # Info
    info = client.info()
    print(f"API: {info['nome']} v{info['versao']}\n")

    # Fontes
    fontes = client.listar_fontes()
    print(f"Fontes disponíveis: {len(fontes['fontes'])}\n")

    # Pesquisa
    print("=== Pesquisa: diabetes ===")
    resultados = client.pesquisar("diabetes", limit=5)
    print(f"Total: {resultados['total']} resultados\n")

    for r in resultados['resultados'][:3]:
        print(f"Título: {r['titulo']}")
        print(f"Citação: {r['citacao_abnt']}")
        print(f"Fonte: {r['fonte']}\n")

    # Resposta formatada
    print("=== Resposta: tratamento hipertensão ===")
    resposta = client.resposta("tratamento hipertensão")
    print(resposta['texto'])
    print("\nReferências:")
    for ref in resposta['referencias'][:3]:
        print(f"  • {ref}")
