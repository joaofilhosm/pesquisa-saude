"""
Teste direto da API de Pesquisa - sem depender dos servidores HTTP
"""
import asyncio
import sys
sys.path.insert(0, 'backend-python')

from scrapers.ministerio_saude import MinisterioSaudeScraper
from scrapers.sbmfc import SBMFCScraper
from scrapers.sbp import SBPScraper
from scrapers.sbpt import SBPTScraper
from scrapers.sbc import SBCScraper
from scrapers.scielo import SciELOScraper
from scrapers.lilacs import LILACSScraper
from scrapers.pubmed import PubMedScraper
from abnt.formatador import ABNTFormatador, Artigo, formatador


async def pesquisar(query: str, limit: int = 20):
    """Pesquisa unificada em todas as fontes"""
    scrapers = {
        'ministerio': MinisterioSaudeScraper(),
        'sbmfc': SBMFCScraper(),
        'sbp': SBPScraper(),
        'sbpt': SBPTScraper(),
        'sbc': SBCScraper(),
        'scielo': SciELOScraper(),
        'lilacs': LILACSScraper(),
        'pubmed': PubMedScraper()
    }

    # Executar buscas em paralelo
    tarefas = []
    for nome, scraper in scrapers.items():
        if hasattr(scraper, 'buscar'):
            tarefas.append(scraper.buscar(query))
        elif hasattr(scraper, 'buscar_protocolos'):
            tarefas.append(scraper.buscar_protocolos(query))

    resultados = await asyncio.gather(*tarefas, return_exceptions=True)

    # Consolidar
    todos = []
    for r in resultados:
        if isinstance(r, list):
            todos.extend(r)

    # Remover duplicatas
    vistos = set()
    unicos = []
    for r in todos:
        chave = r.get('titulo', '')[:50]
        if chave not in vistos:
            vistos.add(chave)
            unicos.append(r)

    return unicos[:limit]


def main():
    print("=" * 70)
    print("  API DE PESQUISA EM SAÚDE - TESTE DIRETO")
    print("=" * 70)

    import sys
    query = sys.argv[1] if len(sys.argv) > 1 else "hipertensão"
    print(f"\nPesquisando por: {query}...\n")

    resultados = asyncio.run(pesquisar(query, limit=20))

    print(f"\n{'='*70}")
    print(f"RESULTADOS: {len(resultados)} encontrados\n")

    for i, r in enumerate(resultados, 1):
        titulo = r.get('titulo', 'S/T')
        fonte = r.get('fonte', 'N/A')
        ano = r.get('ano', 'N/A')
        resumo = r.get('resumo', '')[:200]

        # Formatar citação ABNT
        artigo = Artigo.from_dict(r)
        citacao = formatador.formatar_citacao_curta(artigo)
        referencia = formatador.formatar_referencia(artigo)

        print(f"{i}. {titulo}")
        print(f"   Fonte: {fonte} | Ano: {ano}")
        print(f"   Citação: {citacao}")
        print(f"   Resumo: {resumo}...")
        print(f"   Referência: {referencia}")
        print()

    print("=" * 70)
    print("REFERÊNCIAS COMPLETAS (ABNT):\n")
    for r in resultados:
        artigo = Artigo.from_dict(r)
        ref = formatador.formatar_referencia(artigo)
        print(f"• {ref}")

    print("\n" + "=" * 70)


if __name__ == "__main__":
    main()
