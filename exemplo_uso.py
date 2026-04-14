"""
Exemplo de uso da API de Pesquisa em Saúde

Este script demonstra como:
1. Pesquisar em fontes brasileiras
2. Obter citações ABNT automáticas
3. Filtrar por tipo de fonte
"""

import requests
import json

# Configuração
BASE_URL = "http://localhost:3000"


def pesquisar_simples(termo: str):
    """Pesquisa simples em todas as fontes"""
    print(f"\n{'='*60}")
    print(f"PESQUISA SIMPLES: {termo}")
    print('='*60)

    response = requests.get(
        f"{BASE_URL}/pesquisar",
        params={"q": termo, "limit": 5}
    )

    dados = response.json()

    print(f"\nTotal de resultados: {dados.get('total', 0)}\n")

    for i, resultado in enumerate(dados.get('resultados', []), 1):
        print(f"{i}. {resultado.get('titulo', 'S/T')}")
        print(f"   Fonte: {resultado.get('fonte', 'N/A')}")
        print(f"   Ano: {resultado.get('ano', 'N/A')}")
        print(f"   Citação ABNT: {resultado.get('citacao_abnt', 'N/A')}")
        print()


def pesquisar_com_filtro(termo: str, fontes: list):
    """Pesquisa filtrando fontes específicas"""
    print(f"\n{'='*60}")
    print(f"PESQUISA FILTRADA: {termo}")
    print(f"Fontes: {', '.join(fontes)}")
    print('='*60)

    response = requests.post(
        f"{BASE_URL}/pesquisar",
        json={
            "query": termo,
            "fontes": fontes,
            "ano_min": 2016,
            "incluir_citacoes": True,
            "limit": 5
        }
    )

    dados = response.json()

    for resultado in dados.get('resultados', []):
        print(f"\n- {resultado.get('titulo', 'S/T')}")
        print(f"  {resultado.get('resumo', '')[:200]}...")
        print(f"  {resultado.get('citacao_abnt', '')}")


def gerar_resposta_completa(termo: str):
    """Gera resposta formatada com citações em cada parágrafo"""
    print(f"\n{'='*60}")
    print(f"RESPOSTA FORMATADA: {termo}")
    print('='*60)

    response = requests.post(
        f"{BASE_URL}/resposta",
        json={
            "query": termo,
            "ano_min": 2016,
            "limit": 10
        }
    )

    dados = response.json()

    if dados.get('sucesso'):
        print(f"\n{dados['dados']['texto']}\n")

        print("\nREFERÊNCIAS:")
        print("-"*40)
        for ref in dados['dados']['referencias']:
            print(f"• {ref}")


def buscar_pcdt(termo: str):
    """Busca específica no PCDT do Ministério da Saúde"""
    print(f"\n{'='*60}")
    print(f"PCDT - Ministério da Saúde: {termo}")
    print('='*60)

    response = requests.get(
        f"{BASE_URL}/pcdt",
        params={"termo": termo}
    )

    dados = response.json()

    for resultado in dados.get('resultados', []):
        print(f"\n• {resultado.get('titulo', 'S/T')}")
        print(f"  URL: {resultado.get('url', 'N/A')}")


def main():
    """Executa exemplos de pesquisa"""

    print("\n" + "="*60)
    print("  API DE PESQUISA EM SAÚDE - EXEMPLOS DE USO")
    print("="*60)

    # Exemplo 1: Pesquisa simples sobre diabetes
    pesquisar_simples("diabetes tipo 2 protocolo")

    # Exemplo 2: Pesquisa filtrada (apenas Ministério da Saúde + SBC)
    pesquisar_com_filtro(
        "hipertensão arterial",
        fontes=["ministerio", "sbc"]
    )

    # Exemplo 3: Gerar resposta completa com citações
    gerar_resposta_completa("tratamento hipertensão gestante")

    # Exemplo 4: Buscar no PCDT
    buscar_pcdt("asma diretriz")

    print("\n" + "="*60)
    print("  EXEMPLOS CONCLUÍDOS")
    print("="*60 + "\n")


if __name__ == "__main__":
    try:
        main()
    except requests.exceptions.ConnectionError:
        print("\n[ERRO] Não foi possível conectar à API.")
        print("Verifique se os servidores Python e Node.js estão rodando:")
        print("  - Python: http://localhost:8000")
        print("  - Node.js: http://localhost:3000\n")
    except Exception as e:
        print(f"\n[ERRO] {e}\n")
