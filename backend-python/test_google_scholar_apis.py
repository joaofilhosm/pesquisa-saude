"""
Script de teste para APIs do Google Scholar
Testa separadamente cada uma das 4 APIs:
- SERPAPI_KEY
- SEARCHAPI_KEY
- SCHOLARAPI_KEY
- SERPLY_API_KEY
"""
import asyncio
import os
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


async def main():
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
