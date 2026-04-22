#!/usr/bin/env python3
"""
Script de teste para APIs do Google Scholar
Lê as variáveis de ambiente do runtime (injetadas pelo repo-panel)
"""
import asyncio
import os
import sys

# Adiciona o path correto
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def test_api(nome: str, env_var: str, scraper_class: str, termo: str = "diabetes tipo 2"):
    """Testa uma API específica"""
    api_key = os.getenv(env_var)

    print("\n" + "="*60)
    print(f"🔵 TESTANDO {nome.upper()}")
    print("="*60)

    if not api_key:
        print(f"⚠️  {env_var} NÃO CONFIGURADA")
        print(f"   Configure no repo-panel ou em .env")
        return

    print(f"   {env_var}: ✓ configurada ({api_key[:8]}...{api_key[-4:] if len(api_key) > 12 else '***'})")
    print(f"   Termo: {termo}")

    try:
        if scraper_class == "SerpAPIScraper":
            from scrapers.serpapi import SerpAPIScraper
            scraper = SerpAPIScraper()
        elif scraper_class == "SearchApiScraper":
            from scrapers.searchapi import SearchApiScraper
            scraper = SearchApiScraper()
        elif scraper_class == "ScholarAPIScraper":
            from scrapers.scholarapi import ScholarAPIScraper
            scraper = ScholarAPIScraper()
        elif scraper_class == "SerplyScraper":
            from scrapers.serply import SerplyScraper
            scraper = SerplyScraper()
        else:
            print(f"❌ Scraper desconhecido: {scraper_class}")
            return

        resultados = await scraper.buscar(termo, ano_min=2020)

        print(f"\n✅ RESULTADO:")
        print(f"   Status: SUCESSO")
        print(f"   Resultados: {len(resultados)} artigos")

        if resultados:
            r = resultados[0]
            print(f"\n   📄 Primeiro artigo:")
            print(f"      Título: {r['titulo'][:70]}...")
            print(f"      Ano: {r.get('ano', 'N/A')}")
            if r.get('autores'):
                print(f"      Autor: {r['autores'][0]}")
            print(f"      Fonte: {r.get('fonte', 'N/A')}")
            if r.get('url'):
                print(f"      URL: {r['url'][:60]}...")
            if r.get('doi'):
                print(f"      DOI: {r['doi']}")

    except Exception as e:
        print(f"\n❌ ERRO: {e}")
        import traceback
        traceback.print_exc()


async def main():
    print("\n" + "#"*60)
    print("# TESTE DAS APIs GOOGLE SCHOLAR (Runtime)")
    print("# Verifica variáveis injetadas pelo repo-panel")
    print("#"*60)

    # Lista de APIs para testar
    apis = [
        ("SerpAPI", "SERPAPI_KEY", "SerpAPIScraper"),
        ("SearchApi.io", "SEARCHAPI_KEY", "SearchApiScraper"),
        ("ScholarAPI.net", "SCHOLARAPI_KEY", "ScholarAPIScraper"),
        ("Serply.io", "SERPLY_API_KEY", "SerplyScraper"),
    ]

    # Verifica quais estão configuradas
    print("\n📋 VERIFICAÇÃO DE VARIÁVEIS:")
    configuradas = []
    nao_configuradas = []

    for nome, env_var, _ in apis:
        if os.getenv(env_var):
            configuradas.append(f"✓ {env_var}")
        else:
            nao_configuradas.append(f"✗ {env_var}")

    for item in configuradas:
        print(f"   {item}")
    for item in nao_configuradas:
        print(f"   {item}")

    if not configuradas:
        print("\n⚠️  Nenhuma API key configurada!")
        print("   Verifique se o repo-panel injetou as variáveis.")
        return

    print(f"\n   Total: {len(configuradas)}/{len(apis)} APIs configuradas")

    # Testa cada API configurada
    print("\n" + "="*60)
    print("INICIANDO TESTES...")
    print("="*60)

    for nome, env_var, scraper in apis:
        if os.getenv(env_var):
            await test_api(nome, env_var, scraper)

    print("\n" + "="*60)
    print("✅ TESTES CONCLUÍDOS")
    print("="*60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
