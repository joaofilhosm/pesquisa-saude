"""
Script de teste para APIs do Google Scholar
Testa separadamente cada uma das 4 APIs:
- SERPAPI_KEY
- SEARCHAPI_KEY
- SCHOLARAPI_KEY
- SERPLY_API_KEY

Uso:
  # Com variáveis de ambiente:
  export SERPAPI_KEY="sua-chave"
  python test_google_scholar_apis.py

  # Ou via linha de comando:
  python test_google_scholar_apis.py --api serpapi --key "sua-chave"
  python test_google_scholar_apis.py --api searchapi --key "sua-chave"
  python test_google_scholar_apis.py --api scholarapi --key "sua-chave"
  python test_google_scholar_apis.py --api serply --key "sua-chave"
"""
import asyncio
import os
import sys
import argparse
from dotenv import load_dotenv

load_dotenv()

async def test_serpapi():
    """Testa SerpAPI"""
    print("\n" + "="*60)
    print("🔵 TESTANDO SERPAPI")
    print("="*60)

    api_key = os.getenv("SERPAPI_KEY")
    if not api_key:
        print("❌ SERPAPI_KEY não configurada")
        return

    try:
        from scrapers.serpapi import SerpAPIScraper
        scraper = SerpAPIScraper()
        resultados = await scraper.buscar("diabetes tipo 2", ano_min=2020)

        print(f"✅ Sucesso!")
        print(f"   Resultados encontrados: {len(resultados)}")
        if resultados:
            print(f"   Primeiro resultado:")
            print(f"   - Título: {resultados[0]['titulo'][:80]}...")
            print(f"   - Ano: {resultados[0].get('ano', 'N/A')}")
            print(f"   - Fonte: {resultados[0].get('fonte', 'N/A')}")
            print(f"   - URL: {resultados[0].get('url', 'N/A')[:60]}...")
    except Exception as e:
        print(f"❌ Erro: {e}")


async def test_searchapi():
    """Testa SearchApi.io"""
    print("\n" + "="*60)
    print("🟢 TESTANDO SEARCHAPI.IO")
    print("="*60)

    api_key = os.getenv("SEARCHAPI_KEY")
    if not api_key:
        print("❌ SEARCHAPI_KEY não configurada")
        return

    try:
        from scrapers.searchapi import SearchApiScraper
        scraper = SearchApiScraper()
        resultados = await scraper.buscar("diabetes tipo 2", ano_min=2020)

        print(f"✅ Sucesso!")
        print(f"   Resultados encontrados: {len(resultados)}")
        if resultados:
            print(f"   Primeiro resultado:")
            print(f"   - Título: {resultados[0]['titulo'][:80]}...")
            print(f"   - Ano: {resultados[0].get('ano', 'N/A')}")
            print(f"   - Fonte: {resultados[0].get('fonte', 'N/A')}")
            print(f"   - URL: {resultados[0].get('url', 'N/A')[:60]}...")
    except Exception as e:
        print(f"❌ Erro: {e}")


async def test_scholarapi():
    """Testa ScholarAPI.net"""
    print("\n" + "="*60)
    print("🟡 TESTANDO SCHOLARAPI.NET")
    print("="*60)

    api_key = os.getenv("SCHOLARAPI_KEY")
    if not api_key:
        print("❌ SCHOLARAPI_KEY não configurada")
        return

    try:
        from scrapers.scholarapi import ScholarAPIScraper
        scraper = ScholarAPIScraper()
        resultados = await scraper.buscar("diabetes tipo 2", ano_min=2020)

        print(f"✅ Sucesso!")
        print(f"   Resultados encontrados: {len(resultados)}")
        if resultados:
            print(f"   Primeiro resultado:")
            print(f"   - Título: {resultados[0]['titulo'][:80]}...")
            print(f"   - Ano: {resultados[0].get('ano', 'N/A')}")
            print(f"   - Fonte: {resultados[0].get('fonte', 'N/A')}")
            print(f"   - URL: {resultados[0].get('url', 'N/A')[:60]}...")
    except Exception as e:
        print(f"❌ Erro: {e}")


async def test_serply():
    """Testa Serply.io"""
    print("\n" + "="*60)
    print("🟣 TESTANDO SERPLY.IO")
    print("="*60)

    api_key = os.getenv("SERPLY_API_KEY")
    if not api_key:
        print("❌ SERPLY_API_KEY não configurada")
        return

    try:
        from scrapers.serply import SerplyScraper
        scraper = SerplyScraper()
        resultados = await scraper.buscar("diabetes tipo 2", ano_min=2020)

        print(f"✅ Sucesso!")
        print(f"   Resultados encontrados: {len(resultados)}")
        if resultados:
            print(f"   Primeiro resultado:")
            print(f"   - Título: {resultados[0]['titulo'][:80]}...")
            print(f"   - Ano: {resultados[0].get('ano', 'N/A')}")
            print(f"   - Fonte: {resultados[0].get('fonte', 'N/A')}")
            print(f"   - URL: {resultados[0].get('url', 'N/A')[:60]}...")
    except Exception as e:
        print(f"❌ Erro: {e}")


async def test_single_api(api_name: str, api_key: str, termo: str = "diabetes tipo 2"):
    """Testa uma API específica com a chave fornecida"""

    print("\n" + "="*60)
    print(f"🔵 TESTANDO {api_name.upper()}")
    print("="*60)
    print(f"   Termo: {termo}")
    print(f"   API Key: {api_key[:10]}...{api_key[-4:]}")

    try:
        if api_name == "serpapi":
            from scrapers.serpapi import SerpAPIScraper
            os.environ["SERPAPI_KEY"] = api_key
            scraper = SerpAPIScraper()
        elif api_name == "searchapi":
            from scrapers.searchapi import SearchApiScraper
            os.environ["SEARCHAPI_KEY"] = api_key
            scraper = SearchApiScraper()
        elif api_name == "scholarapi":
            from scrapers.scholarapi import ScholarAPIScraper
            os.environ["SCHOLARAPI_KEY"] = api_key
            scraper = ScholarAPIScraper()
        elif api_name == "serply":
            from scrapers.serply import SerplyScraper
            os.environ["SERPLY_API_KEY"] = api_key
            scraper = SerplyScraper()
        else:
            print(f"❌ API desconhecida: {api_name}")
            return

        resultados = await scraper.buscar(termo, ano_min=2020)

        print(f"\n✅ Sucesso!")
        print(f"   Resultados encontrados: {len(resultados)}")
        if resultados:
            print(f"\n   Primeiro resultado:")
            print(f"   - Título: {resultados[0]['titulo'][:80]}...")
            print(f"   - Ano: {resultados[0].get('ano', 'N/A')}")
            print(f"   - Autores: {resultados[0].get('autores', ['N/A'])[0] if resultados[0].get('autores') else 'N/A'}")
            print(f"   - Fonte: {resultados[0].get('fonte', 'N/A')}")
            print(f"   - URL: {resultados[0].get('url', 'N/A')[:60] if resultados[0].get('url') else 'N/A'}...")
            print(f"   - DOI: {resultados[0].get('doi', 'N/A')}")
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()


async def main():
    parser = argparse.ArgumentParser(description="Teste das APIs do Google Scholar")
    parser.add_argument("--api", choices=["serpapi", "searchapi", "scholarapi", "serply"],
                        help="API específica para testar")
    parser.add_argument("--key", help="Chave da API para teste individual")
    parser.add_argument("--termo", default="diabetes tipo 2", help="Termo de busca (padrão: diabetes tipo 2)")

    args = parser.parse_args()

    # Teste individual
    if args.api and args.key:
        await test_single_api(args.api, args.key, args.termo)
        return

    # Teste completo de todas as APIs
    print("\n" + "#"*60)
    print("# TESTE DAS APIs DO GOOGLE SCHOLAR")
    print("#"*60)

    print("\n📋 Verificando variáveis de ambiente:")
    print(f"   SERPAPI_KEY: {'✓ configurada' if os.getenv('SERPAPI_KEY') else '✗ não configurada'}")
    print(f"   SEARCHAPI_KEY: {'✓ configurada' if os.getenv('SEARCHAPI_KEY') else '✗ não configurada'}")
    print(f"   SCHOLARAPI_KEY: {'✓ configurada' if os.getenv('SCHOLARAPI_KEY') else '✗ não configurada'}")
    print(f"   SERPLY_API_KEY: {'✓ configurada' if os.getenv('SERPLY_API_KEY') else '✗ não configurada'}")

    await test_serpapi()
    await test_searchapi()
    await test_scholarapi()
    await test_serply()

    print("\n" + "="*60)
    print("✅ TESTES CONCLUÍDOS")
    print("="*60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
