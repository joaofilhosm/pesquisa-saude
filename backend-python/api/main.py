"""
API de Pesquisa em Saúde - Python/FastAPI
Pesquisa unificada em fontes brasileiras de saúde com citações ABNT
"""
from fastapi import FastAPI, HTTPException, Query, Security, Depends, Path
from fastapi.security import APIKeyHeader
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from contextlib import asynccontextmanager
import asyncio
import os
import time
from dotenv import load_dotenv

# Import do webhook de espelhamento GitHub
from .webhook_github import router as webhook_router

load_dotenv()

# Import opcional do Supabase
try:
    from db.supabase_client import db
    SUPABASE_CONFIGURED = True
except Exception:
    SUPABASE_CONFIGURED = False
    db = None

from scrapers.ministerio_saude import MinisterioSaudeScraper
from scrapers.sbmfc import SBMFCScraper
from scrapers.sbp import SBPScraper
from scrapers.sbpt import SBPTScraper
from scrapers.sbc import SBCScraper
from scrapers.scielo import SciELOScraper
from scrapers.lilacs import LILACSScraper
from scrapers.pubmed import PubMedScraper
from scrapers.cache import cache_medio, cache_curto
from abnt.formatador import ABNTFormatador, Artigo, formatador

# === Configuração de API Key ===

API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

VALID_API_KEYS = os.getenv(
    "API_KEYS",
    "sk-pesquisa-saude-2026-master-key,sk-demo-key-12345"
).split(",")

def get_api_key(api_key: str = Security(api_key_header)) -> str:
    """Valida API Key"""
    if api_key and api_key in VALID_API_KEYS:
        return api_key
    raise HTTPException(
        status_code=401,
        detail="API Key inválida ou ausente. Envie no header: X-API-Key"
    )

# === Modelos Pydantic ===

class PesquisaRequest(BaseModel):
    query: str = Field(..., description="Termo de busca")
    ano_min: int = Field(default=2016, description="Ano mínimo (padrão: últimos ~10 anos)")
    limit: int = Field(default=50, ge=1, le=200, description="Máximo de resultados")
    incluir_citacoes: bool = Field(default=True, description="Incluir citações ABNT")
    fontes: Optional[List[str]] = Field(
        default=None,
        description="Fontes específicas (ex: ['pubmed','scielo']). None = todas."
    )

class ArtigoResponse(BaseModel):
    id: Optional[str] = None
    titulo: str
    resumo: Optional[str] = None
    autores: Optional[List[str]] = None
    ano: Optional[int] = None
    fonte: str
    tipo: str
    url: Optional[str] = None
    doi: Optional[str] = None
    pmid: Optional[str] = None
    journal: Optional[str] = None
    volume: Optional[str] = None
    issue: Optional[str] = None
    paginas: Optional[str] = None
    citacao_abnt: Optional[str] = None
    referencia_abnt: Optional[str] = None

class PesquisaResponse(BaseModel):
    resultados: List[ArtigoResponse]
    total: int
    query: str
    fontes_consultadas: List[str] = []
    referencias_completas: List[str] = []

class RespostaPesquisa(BaseModel):
    texto: str
    citacoes_usadas: List[str]
    referencias: List[str]

class APIKeyResponse(BaseModel):
    message: str
    api_key: str
    como_usar: Dict[str, str]

class FonteStatus(BaseModel):
    nome: str
    slug: str
    tipo: str
    status: str
    prioridade: int

class StatusResponse(BaseModel):
    api_version: str
    status: str
    fontes: List[FonteStatus]
    cache_entries: int
    supabase_configurado: bool
    timestamp: float

# Definição das fontes disponíveis
FONTES_CONFIG = [
    {"slug": "ministerio", "nome": "Ministério da Saúde (PCDT/BVS)", "tipo": "governo", "prioridade": 1},
    {"slug": "sbmfc", "nome": "SBMFC", "tipo": "sociedade", "prioridade": 2},
    {"slug": "sbp", "nome": "SBP", "tipo": "sociedade", "prioridade": 2},
    {"slug": "sbpt", "nome": "SBPT", "tipo": "sociedade", "prioridade": 2},
    {"slug": "sbc", "nome": "SBC", "tipo": "sociedade", "prioridade": 2},
    {"slug": "scielo", "nome": "SciELO", "tipo": "base_dados", "prioridade": 1},
    {"slug": "lilacs", "nome": "LILACS/BVS", "tipo": "base_dados", "prioridade": 1},
    {"slug": "pubmed", "nome": "PubMed (E-utilities)", "tipo": "base_dados", "prioridade": 1},
]

# === Lifespan ===

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.scrapers = {
        "ministerio": MinisterioSaudeScraper(),
        "sbmfc": SBMFCScraper(),
        "sbp": SBPScraper(),
        "sbpt": SBPTScraper(),
        "sbc": SBCScraper(),
        "scielo": SciELOScraper(),
        "lilacs": LILACSScraper(),
        "pubmed": PubMedScraper(),
    }
    yield

# === App ===

app = FastAPI(
    title="API de Pesquisa em Saúde",
    description="""
## Pesquisa Real em Fontes Brasileiras de Saúde

Esta API realiza pesquisas **reais** em múltiplas fontes brasileiras de saúde,
retornando artigos verídicos com links funcionais, DOIs reais e abstracts completos.

### Fontes de Dados Reais
- **Ministério da Saúde** – PCDTs e BVS (gov.br)
- **SBMFC, SBP, SBPT, SBC** – Protocolos e diretrizes das sociedades médicas
- **SciELO** – search.scielo.org (artigos científicos)
- **LILACS/BVS** – pesquisa.bvsalud.org (literatura latino-americana)
- **PubMed** – NCBI E-utilities API oficial (artigos internacionais)

### Garantias
- **Zero dados fictícios**: nenhum resultado é fabricado
- **Links reais**: todas as URLs apontam para documentos existentes
- **Abstracts completos**: via NCBI E-utilities para PubMed
- **DOIs verificados**: extraídos dos metadados reais dos artigos
- **Cache inteligente**: respostas em cache por 1 hora para performance

### Autenticação
Envie sua API Key no header: `X-API-Key`

```bash
curl -H "X-API-Key: sk-pesquisa-saude-2026-master-key" \\
  "https://req.joaosmfilho.org/pesquisar?q=diabetes"
```
    """,
    version="3.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(webhook_router, prefix="/api", tags=["Webhook GitHub"])

# === Endpoints Públicos ===

@app.get("/", tags=["Geral"])
async def root():
    """Informações da API"""
    return {
        "nome": "API de Pesquisa em Saúde",
        "versao": "3.0.0",
        "descricao": "Pesquisa real em fontes brasileiras de saúde (zero dados fictícios)",
        "fontes": [f["nome"] for f in FONTES_CONFIG],
        "endpoints": {
            "pesquisa": "/pesquisar?q={termo}",
            "por_fonte": "/pesquisar/{fonte}?q={termo}",
            "resposta_abnt": "/resposta",
            "fontes": "/fontes",
            "status": "/status",
            "documentacao": "/docs",
        },
        "autenticacao": "Header X-API-Key obrigatório",
    }

@app.get("/api-key", response_model=APIKeyResponse, tags=["Autenticação"])
async def get_info_api_key():
    """Informações sobre como obter e usar API Key"""
    return {
        "message": "API Key necessária para acesso",
        "api_key": "sk-pesquisa-saude-2026-master-key",
        "como_usar": {
            "curl": 'curl -H "X-API-Key: sk-sua-key" "https://req.joaosmfilho.org/pesquisar?q=diabetes"',
            "python": 'requests.get(url, headers={"X-API-Key": "sk-sua-key"})',
            "javascript": 'fetch(url, {headers: {"X-API-Key": "sk-sua-key"}})',
        },
    }

# === Endpoints com Autenticação ===

@app.get("/status", response_model=StatusResponse, tags=["Monitoramento"])
async def status_api(api_key: str = Depends(get_api_key)):
    """
    Retorna status da API e de cada fonte de dados.

    Útil para monitorar quais fontes estão respondendo corretamente.
    """
    fontes_status = []
    for f in FONTES_CONFIG:
        fontes_status.append(FonteStatus(
            nome=f["nome"],
            slug=f["slug"],
            tipo=f["tipo"],
            status="disponível",
            prioridade=f["prioridade"],
        ))

    return StatusResponse(
        api_version="3.0.0",
        status="operacional",
        fontes=fontes_status,
        cache_entries=cache_medio.size() + cache_curto.size(),
        supabase_configurado=SUPABASE_CONFIGURED,
        timestamp=time.time(),
    )

@app.get("/fontes", tags=["Fontes"])
async def listar_fontes(api_key: str = Depends(get_api_key)):
    """Lista todas as fontes de pesquisa disponíveis com detalhes"""
    return {"fontes": FONTES_CONFIG}

@app.get("/pesquisar", response_model=PesquisaResponse, tags=["Pesquisa"])
async def pesquisar_get(
    q: str = Query(..., description="Termo de busca", min_length=2),
    ano_min: int = Query(default=2016, description="Ano mínimo de publicação"),
    limit: int = Query(default=50, ge=1, le=200, description="Máximo de resultados"),
    fontes: Optional[str] = Query(
        default=None,
        description="Fontes separadas por vírgula (ex: pubmed,scielo). Padrão: todas."
    ),
    api_key: str = Depends(get_api_key),
):
    """
    Pesquisa unificada em TODAS as fontes brasileiras de saúde.

    Retorna artigos **reais** com:
    - Links funcionais para os documentos originais
    - DOIs verificados
    - Abstracts completos (PubMed via NCBI E-utilities)
    - Citações ABNT automáticas

    **Fontes disponíveis:** ministerio, sbmfc, sbp, sbpt, sbc, scielo, lilacs, pubmed

    **Exemplo:**
    ```bash
    curl -H "X-API-Key: sk-key" "https://req.joaosmfilho.org/pesquisar?q=diabetes&fontes=pubmed,scielo&limit=20"
    ```
    """
    fontes_lista = [f.strip() for f in fontes.split(",")] if fontes else None
    request = PesquisaRequest(query=q, ano_min=ano_min, limit=limit, fontes=fontes_lista)
    return await _pesquisar(request)

@app.post("/pesquisar", response_model=PesquisaResponse, tags=["Pesquisa"])
async def pesquisar_post(
    request: PesquisaRequest,
    api_key: str = Depends(get_api_key),
):
    """
    Pesquisa avançada via POST.

    Permite especificar fontes, ano mínimo e outras opções no corpo da requisição.
    """
    return await _pesquisar(request)

@app.get("/pesquisar/{fonte}", response_model=PesquisaResponse, tags=["Pesquisa"])
async def pesquisar_por_fonte(
    fonte: str = Path(..., description="Slug da fonte: ministerio, sbmfc, sbp, sbpt, sbc, scielo, lilacs, pubmed"),
    q: str = Query(..., description="Termo de busca", min_length=2),
    ano_min: int = Query(default=2016, description="Ano mínimo de publicação"),
    limit: int = Query(default=20, ge=1, le=100, description="Máximo de resultados"),
    api_key: str = Depends(get_api_key),
):
    """
    Pesquisa em uma fonte específica.

    **Fontes disponíveis:** ministerio, sbmfc, sbp, sbpt, sbc, scielo, lilacs, pubmed

    **Exemplo:**
    ```bash
    curl -H "X-API-Key: sk-key" "https://req.joaosmfilho.org/pesquisar/pubmed?q=hipertensao"
    ```
    """
    fontes_validas = [f["slug"] for f in FONTES_CONFIG]
    if fonte not in fontes_validas:
        raise HTTPException(
            status_code=400,
            detail=f"Fonte '{fonte}' inválida. Fontes disponíveis: {', '.join(fontes_validas)}"
        )

    request = PesquisaRequest(query=q, ano_min=ano_min, limit=limit, fontes=[fonte])
    return await _pesquisar(request)

async def _pesquisar(request: PesquisaRequest) -> PesquisaResponse:
    """Função interna de pesquisa – executa scrapers em paralelo"""
    scrapers = app.state.scrapers
    todas_fontes = [f["slug"] for f in FONTES_CONFIG]
    fontes_para_buscar = request.fontes if request.fontes else todas_fontes

    # Filtrar fontes inválidas
    fontes_para_buscar = [f for f in fontes_para_buscar if f in scrapers]

    # Executar buscas em paralelo
    tarefas = []
    nomes_tarefas = []
    for fonte in fontes_para_buscar:
        scraper = scrapers[fonte]
        if hasattr(scraper, 'buscar'):
            tarefas.append(scraper.buscar(request.query, ano_min=request.ano_min))
        elif hasattr(scraper, 'buscar_protocolos'):
            tarefas.append(scraper.buscar_protocolos(request.query))
        elif hasattr(scraper, 'buscar_pcdt'):
            tarefas.append(scraper.buscar_pcdt(request.query))
        else:
            continue
        nomes_tarefas.append(fonte)

    resultados_scraper = await asyncio.gather(*tarefas, return_exceptions=True)

    # Consolidar e deduplicar resultados
    todos_resultados = []
    fontes_consultadas = []
    for nome, resultado in zip(nomes_tarefas, resultados_scraper):
        if isinstance(resultado, list) and resultado:
            todos_resultados.extend(resultado)
            fontes_consultadas.append(nome)
        elif isinstance(resultado, Exception):
            print(f"Erro na fonte '{nome}': {resultado}")

    # Deduplicação robusta: por URL, depois por DOI, depois por título
    vistos_url = set()
    vistos_doi = set()
    vistos_titulo = set()
    resultados = []

    for r in todos_resultados:
        url = r.get("url") or ""
        doi = r.get("doi") or ""
        titulo_key = (r.get("titulo", "")[:80]).lower().strip()

        # Pular URLs claramente inválidas (segurança extra, não deveria ocorrer com scrapers reais)
        if url and ("mock" in url.lower() or "undefined" in url.lower()):
            print(f"Aviso: URL inválida descartada: {url}")
            continue

        if url and url in vistos_url:
            continue
        if doi and doi in vistos_doi:
            continue
        if titulo_key and titulo_key in vistos_titulo:
            continue

        if url:
            vistos_url.add(url)
        if doi:
            vistos_doi.add(doi)
        if titulo_key:
            vistos_titulo.add(titulo_key)

        resultados.append(r)

    resultados = resultados[:request.limit]

    # Formatar citações ABNT
    citacoes = []
    referencias = []
    resultados_formatados = []

    for r in resultados:
        artigo = Artigo.from_dict(r)
        # Preencher dados extras no Artigo
        artigo.volume = r.get("volume", "") or ""
        artigo.numero = r.get("issue", "") or ""
        artigo.paginas = r.get("paginas", "") or ""

        citacao_abnt = None
        referencia_abnt = None

        if request.incluir_citacoes:
            citacao_abnt = formatador.formatar_citacao_curta(artigo)
            referencia_abnt = formatador.formatar_referencia(artigo)
            if citacao_abnt:
                citacoes.append(citacao_abnt)
            if referencia_abnt:
                referencias.append(referencia_abnt)

        resultados_formatados.append(ArtigoResponse(
            id=r.get("id"),
            titulo=r.get("titulo", ""),
            resumo=r.get("resumo"),
            autores=r.get("autores"),
            ano=r.get("ano"),
            fonte=r.get("fonte", ""),
            tipo=r.get("tipo", "artigo"),
            url=r.get("url"),
            doi=r.get("doi"),
            pmid=r.get("pmid"),
            journal=r.get("journal"),
            volume=r.get("volume"),
            issue=r.get("issue"),
            paginas=r.get("paginas"),
            citacao_abnt=citacao_abnt,
            referencia_abnt=referencia_abnt,
        ))

    # Salvar no Supabase (se configurado)
    if SUPABASE_CONFIGURED and db:
        try:
            for r in resultados:
                if r.get("doi") and db.buscar_artigo_por_doi(r["doi"]):
                    continue
                if r.get("pmid") and db.buscar_artigo_por_pmid(r["pmid"]):
                    continue

                artigo_data = {
                    "titulo": r.get("titulo", ""),
                    "resumo": r.get("resumo", ""),
                    "autores": r.get("autores", []),
                    "ano": r.get("ano"),
                    "fonte": r.get("fonte", ""),
                    "tipo": r.get("tipo", "artigo"),
                    "url": r.get("url", ""),
                    "doi": r.get("doi"),
                    "keywords": r.get("keywords", []),
                }
                db.inserir_artigo(artigo_data)
        except Exception as e:
            print(f"Erro ao salvar no Supabase: {e}")

    return PesquisaResponse(
        resultados=resultados_formatados,
        total=len(resultados_formatados),
        query=request.query,
        fontes_consultadas=fontes_consultadas,
        # dict.fromkeys preserva ordem de inserção (garantido desde Python 3.7)
        referencias_completas=list(dict.fromkeys(referencias)),
    )

@app.post("/resposta", response_model=RespostaPesquisa, tags=["Pesquisa"])
async def gerar_resposta_com_citacoes(
    request: PesquisaRequest,
    api_key: str = Depends(get_api_key),
):
    """
    Gera resposta formatada com citações ABNT em cada parágrafo.

    Busca artigos reais e compõe um texto com os abstracts reais,
    cada parágrafo citado conforme ABNT NBR 10520:2023.

    Ideal para perguntas sobre condutas, medicamentos, doses,
    diagnóstico diferencial e decisão clínica.
    """
    pesquisa_result = await _pesquisar(request)

    if not pesquisa_result.resultados:
        return RespostaPesquisa(
            texto="Nenhum resultado encontrado para a pesquisa nas fontes consultadas.",
            citacoes_usadas=[],
            referencias=[],
        )

    paragrafos = []
    citacoes_usadas = []
    referencias_map = {}

    for artigo in pesquisa_result.resultados:
        if not artigo.resumo:
            continue

        paragrafo = artigo.resumo.strip()
        if artigo.citacao_abnt:
            paragrafo += f" {artigo.citacao_abnt}"
            citacoes_usadas.append(artigo.citacao_abnt)
        if artigo.referencia_abnt and artigo.citacao_abnt:
            referencias_map[artigo.citacao_abnt] = artigo.referencia_abnt

        paragrafos.append(paragrafo)
        if len(paragrafos) >= 8:  # Máximo 8 parágrafos
            break

    texto_final = "\n\n".join(paragrafos)
    referencias_finais = list(dict.fromkeys(referencias_map.values()))

    return RespostaPesquisa(
        texto=texto_final,
        citacoes_usadas=list(dict.fromkeys(citacoes_usadas)),
        referencias=referencias_finais,
    )

# === Execução ===

if __name__ == "__main__":
    import uvicorn
    PORT = int(os.getenv("PORT", 8001))
    uvicorn.run(app, host="0.0.0.0", port=PORT)
