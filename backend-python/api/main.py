"""
API de Pesquisa em Saúde - Python/FastAPI
Pesquisa unificada em fontes brasileiras de saúde com citações ABNT
"""
from fastapi import FastAPI, HTTPException, Query, Security, Depends
from fastapi.security import APIKeyHeader
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from contextlib import asynccontextmanager
import asyncio
import os
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
from abnt.formatador import ABNTFormatador, Artigo, formatador

# === Configuração de API Key ===

API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

# API Keys válidas (em produção, usar banco de dados ou variável de ambiente)
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
    ano_min: int = Field(default=2016, description="Ano mínimo (últimos 10 anos)")
    limit: int = Field(default=50, description="Máximo de resultados")
    incluir_citacoes: bool = Field(default=True, description="Incluir citações ABNT")

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
    citacao_abnt: Optional[str] = None
    referencia_abnt: Optional[str] = None

class PesquisaResponse(BaseModel):
    resultados: List[ArtigoResponse]
    total: int
    query: str
    referencias_completas: List[str] = []

class RespostaPesquisa(BaseModel):
    texto: str
    citacoes_usadas: List[str]
    referencias: List[str]

class APIKeyResponse(BaseModel):
    message: str
    api_key: str
    como_usar: Dict[str, str]

# === Lifespan ===

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    app.state.scrapers = {
        "ministerio": MinisterioSaudeScraper(),
        "sbmfc": SBMFCScraper(),
        "sbp": SBPScraper(),
        "sbpt": SBPTScraper(),
        "sbc": SBCScraper(),
        "scielo": SciELOScraper(),
        "lilacs": LILACSScraper(),
        "pubmed": PubMedScraper()
    }
    yield

# === App ===

app = FastAPI(
    title="API de Pesquisa em Saúde",
    description="""
## Pesquisa em Fontes Brasileiras de Saúde

Esta API realiza pesquisas unificadas em múltiplas fontes brasileiras de saúde:

### Fontes Oficiais
- Ministério da Saúde (PCDT, BVS, ANVISA)

### Sociedades Médicas
- SBMFC, SBP, SBPT, SBC

### Bases Científicas
- SciELO, LILACS, PubMed

### Recursos
- **Citações ABNT automáticas** em cada resultado
- **Últimos 10 anos** por padrão
- **Priorização de fontes brasileiras**

### Autenticação
Envie sua API Key no header: `X-API-Key`

Exemplo:
```bash
curl -H "X-API-Key: sk-sua-key" "http://localhost:8001/pesquisar?q=diabetes"
```
    """,
    version="2.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registrar webhook do GitHub
app.include_router(webhook_router, prefix="/api", tags=["Webhook GitHub"])

# === Endpoints Públicos (sem autenticação) ===

@app.get("/", tags=["Geral"])
async def root():
    """Informações da API"""
    return {
        "nome": "API de Pesquisa em Saúde",
        "versao": "2.0.0",
        "fontes": [
            "Ministério da Saúde (PCDT, BVS)",
            "ANVISA",
            "SBMFC", "SBP", "SBPT", "SBC",
            "SciELO", "LILACS", "PubMed"
        ],
        "documentacao": "/docs",
        "como_obter_key": "/api-key"
    }

@app.get("/api-key", response_model=APIKeyResponse, tags=["Autenticação"])
async def get_info_api_key():
    """
    Informações sobre como obter e usar API Key

    Em produção, registre-se para obter sua chave única.
    """
    return {
        "message": "API Key necessária para acesso",
        "api_key": "sk-pesquisa-saude-2026-master-key",
        "como_usar": {
            "curl": 'curl -H "X-API-Key: sk-sua-key" "http://localhost:8001/pesquisar?q=diabetes"',
            "python": 'requests.get(url, headers={"X-API-Key": "sk-sua-key"})',
            "javascript": 'fetch(url, {headers: {"X-API-Key": "sk-sua-key"}})'
        }
    }

# === Endpoints com Autenticação ===

@app.get("/fontes", response_model=Dict, tags=["Fontes"])
async def listar_fontes(api_key: str = Depends(get_api_key)):
    """Lista todas as fontes de pesquisa disponíveis"""
    if SUPABASE_CONFIGURED and db:
        try:
            return {"fontes": db.listar_fontes()}
        except Exception:
            pass

    return {
        "fontes": [
            {"nome": "Ministério da Saúde - PCDT", "tipo": "ministerio", "prioridade": 1},
            {"nome": "BVS", "tipo": "ministerio", "prioridade": 1},
            {"nome": "ANVISA", "tipo": "ministerio", "prioridade": 2},
            {"nome": "SBMFC", "tipo": "sociedade", "prioridade": 2},
            {"nome": "SBP", "tipo": "sociedade", "prioridade": 2},
            {"nome": "SBPT", "tipo": "sociedade", "prioridade": 2},
            {"nome": "SBC", "tipo": "sociedade", "prioridade": 2},
            {"nome": "SciELO", "tipo": "base_dados", "prioridade": 1},
            {"nome": "LILACS", "tipo": "base_dados", "prioridade": 1},
            {"nome": "PubMed", "tipo": "base_dados", "prioridade": 2},
        ]
    }

@app.get("/pesquisar", response_model=PesquisaResponse, tags=["Pesquisa"])
async def pesquisar_get(
    q: str = Query(..., description="Termo de busca"),
    ano_min: int = Query(default=2016, description="Ano mínimo"),
    limit: int = Query(default=50, description="Máximo de resultados"),
    api_key: str = Depends(get_api_key)
):
    """
    Pesquisa unificada em TODAS as fontes brasileiras de saúde

    Retorna resultados de: Ministério da Saúde, BVS, ANVISA, SBMFC, SBP,
    SBPT, SBC, SciELO, LILACS, PubMed - tudo em uma única chamada.

    **Exemplo:**
    ```bash
    curl -H "X-API-Key: sk-key" "http://localhost:8001/pesquisar?q=diabetes&limit=10"
    ```
    """
    request = PesquisaRequest(query=q, ano_min=ano_min, limit=limit)
    return await _pesquisar(request)

@app.post("/pesquisar", response_model=PesquisaResponse, tags=["Pesquisa"])
async def pesquisar_post(
    request: PesquisaRequest,
    api_key: str = Depends(get_api_key)
):
    """
    Pesquisa avançada (POST)

    Permite enviar parâmetros no corpo da requisição.
    """
    return await _pesquisar(request)

async def _pesquisar(request: PesquisaRequest) -> PesquisaResponse:
    """Função interna de pesquisa"""
    resultados = []
    scrapers = app.state.scrapers

    # Busca em TODAS as fontes simultaneamente
    todas_fontes = ["ministerio", "sbmfc", "sbp", "sbpt", "sbc", "scielo", "lilacs", "pubmed"]
    fontes_para_buscar = request.fontes if hasattr(request, 'fontes') else todas_fontes

    # Executar buscas em paralelo
    tarefas = []
    for fonte in fontes_para_buscar:
        if fonte in scrapers:
            scraper = scrapers[fonte]
            if hasattr(scraper, 'buscar'):
                tarefas.append(scraper.buscar(request.query, ano_min=request.ano_min))
            elif hasattr(scraper, 'buscar_protocolos'):
                tarefas.append(scraper.buscar_protocolos(request.query))

    resultados_scraper = await asyncio.gather(*tarefas, return_exceptions=True)

    # Consolidar resultados
    todos_resultados = []
    for resultado in resultados_scraper:
        if isinstance(resultado, list):
            todos_resultados.extend(resultado)

    # Remover duplicatas
    vistos = set()
    for r in todos_resultados:
        chave = r.get("titulo", "")[:50]
        if chave not in vistos:
            vistos.add(chave)
            resultados.append(r)

    resultados = resultados[:request.limit]

    # Formatar citações ABNT
    citacoes = []
    referencias = []
    resultados_formatados = []

    for r in resultados:
        artigo = Artigo.from_dict(r)
        citacao_abnt = None
        referencia_abnt = None

        if request.incluir_citacoes:
            citacao_abnt = formatador.formatar_citacao_curta(artigo)
            referencia_abnt = formatador.formatar_referencia(artigo)
            citacoes.append(citacao_abnt)
            referencias.append(referencia_abnt)

        resultados_formatados.append({
            "id": r.get("id"),
            "titulo": r.get("titulo", ""),
            "resumo": r.get("resumo"),
            "autores": r.get("autores"),
            "ano": r.get("ano"),
            "fonte": r.get("fonte", ""),
            "tipo": r.get("tipo", "artigo"),
            "url": r.get("url"),
            "doi": r.get("doi"),
            "citacao_abnt": citacao_abnt,
            "referencia_abnt": referencia_abnt
        })

    # Salvar no Supabase
    if SUPABASE_CONFIGURED and db:
        try:
            for r in resultados:
                if r.get("doi"):
                    if db.buscar_artigo_por_doi(r.get("doi")):
                        continue
                if r.get("pmid"):
                    if db.buscar_artigo_por_pmid(r.get("pmid")):
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
                    "keywords": r.get("keywords", [])
                }
                artigo_id = db.inserir_artigo(artigo_data)
                r["id"] = artigo_id

                artigo = Artigo.from_dict(r)
                citacao = formatador.formatar_citacao_curta(artigo)
                referencia = formatador.formatar_referencia(artigo)
                db.salvar_referencia(artigo_id, citacao, referencia)

            ids_resultados = [r.get("id") for r in resultados if r.get("id")]
            if ids_resultados:
                db.salvar_busca_cache(request.query, ids_resultados)
        except Exception as e:
            print(f"Erro ao salvar no Supabase: {e}")

    return {
        "resultados": resultados_formatados,
        "total": len(resultados_formatados),
        "query": request.query,
        "referencias_completas": referencias
    }

@app.post("/resposta", response_model=RespostaPesquisa, tags=["Pesquisa"])
async def gerar_resposta_com_citacoes(
    request: PesquisaRequest,
    api_key: str = Depends(get_api_key)
):
    """
    Gera resposta formatada com citações ABNT em cada parágrafo

    Ideal para perguntas sobre condutas, medicamentos, doses,
    diagnóstico diferencial e decisão clínica.
    """
    pesquisa_result = await _pesquisar(request)

    if not pesquisa_result.resultados:
        return {
            "texto": "Nenhum resultado encontrado para a pesquisa.",
            "citacoes_usadas": [],
            "referencias": []
        }

    paragrafos = []
    citacoes_usadas = []
    referencias_map = {}

    for artigo in pesquisa_result.resultados:
        if artigo.resumo:
            paragrafo = artigo.resumo
            if artigo.citacao_abnt:
                paragrafo += f" {artigo.citacao_abnt}"
                citacoes_usadas.append(artigo.citacao_abnt)
            if artigo.referencia_abnt:
                referencias_map[artigo.citacao_abnt] = artigo.referencia_abnt
            paragrafos.append(paragrafo)

    texto_final = "\n\n".join(paragrafos[:5])
    referencias_finais = list(set(referencias_map.values()))

    return {
        "texto": texto_final,
        "citacoes_usadas": citacoes_usadas,
        "referencias": referencias_finais
    }

# === Execução ===

if __name__ == "__main__":
    import uvicorn
    PORT = int(os.getenv("PORT", 8001))
    uvicorn.run(app, host="0.0.0.0", port=PORT)
