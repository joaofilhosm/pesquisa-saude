"""
Script de teste rápido para verificar a API
"""
import requests


def test_health():
    """Testa health check da API Node.js"""
    try:
        r = requests.get("http://localhost:3000/health", timeout=5)
        print("✓ Node.js API:", r.json())
        return True
    except:
        print("✗ Node.js API indisponível")
        return False


def test_python_backend():
    """Testa backend Python"""
    try:
        r = requests.get("http://localhost:8000/", timeout=5)
        print("✓ Python Backend:", r.json().get('nome', 'OK'))
        return True
    except:
        print("✗ Python Backend indisponível")
        return False


def test_pesquisa():
    """Testa pesquisa básica"""
    try:
        r = requests.get(
            "http://localhost:3000/pesquisar",
            params={"q": "diabetes", "limit": 3},
            timeout=30
        )
        dados = r.json()
        print(f"✓ Pesquisa: {dados.get('total', 0)} resultados")
        return True
    except Exception as e:
        print(f"✗ Pesquisa falhou: {e}")
        return False


def test_fontes():
    """Testa listagem de fontes"""
    try:
        r = requests.get("http://localhost:3000/fontes", timeout=5)
        dados = r.json()
        print(f"✓ Fontes: {dados.get('total', 0)} fontes disponíveis")
        return True
    except:
        print("✗ Fontes indisponíveis")
        return False


def main():
    print("\n" + "="*50)
    print("  TESTE DA API DE PESQUISA EM SAÚDE")
    print("="*50 + "\n")

    testes = [
        ("Node.js API", test_health),
        ("Python Backend", test_python_backend),
        ("Fontes", test_fontes),
        ("Pesquisa", test_pesquisa),
    ]

    resultados = []
    for nome, teste in testes:
        print(f"Testando {nome}...", end=" ")
        resultados.append((nome, teste()))

    print("\n" + "="*50)
    print("  RESUMO")
    print("="*50)

    aprovados = sum(1 for _, r in resultados if r)
    total = len(resultados)

    for nome, resultado in resultados:
        status = "✓ OK" if resultado else "✗ FALHOU"
        print(f"  {nome}: {status}")

    print(f"\n  Total: {aprovados}/{total} testes passaram")
    print("="*50 + "\n")

    return aprovados == total


if __name__ == "__main__":
    sucesso = main()
    exit(0 if sucesso else 1)
