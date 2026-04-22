"""
API de Pesquisa em Saúde - Python/FastAPI
Pesquisa unificada em fontes brasileiras de saúde com citações ABNT
"""
from fastapi import FastAPI, HTTPException, Query, Security, Depends, Path
from fastapi.responses import HTMLResponse
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
from scrapers.cochrane import CochraneScraper
from scrapers.redalyc import RedalycScraper
from scrapers.bdtd import BDTDScraper
from scrapers.capes import CapesScraper
from scrapers.semanticscholar import SemanticScholarScraper
from scrapers.openalex import OpenAlexScraper
from scrapers.googlescholar import GoogleScholarScraper
from scrapers.serpapi import SerpAPIScraper
from scrapers.searchapi import SearchApiScraper
from scrapers.scholarapi import ScholarAPIScraper
from scrapers.serply import SerplyScraper
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
    keywords: Optional[List[str]] = None
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
    {"slug": "cochrane", "nome": "Cochrane Library", "tipo": "base_dados", "prioridade": 1},
    {"slug": "redalyc", "nome": "Redalyc", "tipo": "base_dados", "prioridade": 2},
    {"slug": "bdtd", "nome": "BDTD (Teses e Dissertações)", "tipo": "base_dados", "prioridade": 2},
    {"slug": "capes", "nome": "Portal CAPES (CrossRef)", "tipo": "base_dados", "prioridade": 1},
    {"slug": "semanticscholar", "nome": "Semantic Scholar (Allen AI)", "tipo": "base_dados", "prioridade": 1},
    {"slug": "openalex", "nome": "OpenAlex (OurResearch)", "tipo": "base_dados", "prioridade": 1},
    {"slug": "googlescholar", "nome": "Google Scholar (via proxy SOCKS5)", "tipo": "base_dados", "prioridade": 2},
    {"slug": "serpapi", "nome": "Google Scholar (SerpAPI)", "tipo": "api_paga", "prioridade": 1},
    {"slug": "searchapi", "nome": "Google Scholar (SearchApi.io)", "tipo": "api_paga", "prioridade": 1},
    {"slug": "scholarapi", "nome": "Google Scholar (ScholarAPI.net)", "tipo": "api_paga", "prioridade": 1},
    {"slug": "serply", "nome": "Google Scholar (Serply.io)", "tipo": "api_paga", "prioridade": 1},
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
        "cochrane": CochraneScraper(),
        "redalyc": RedalycScraper(),
        "bdtd": BDTDScraper(),
        "capes": CapesScraper(),
        "semanticscholar": SemanticScholarScraper(),
        "openalex": OpenAlexScraper(),
        "googlescholar": GoogleScholarScraper(),
        "serpapi": SerpAPIScraper(),
        "searchapi": SearchApiScraper(),
        "scholarapi": ScholarAPIScraper(),
        "serply": SerplyScraper(),
    }
    yield

# === App ===

app = FastAPI(
    title="API de Pesquisa em Saúde",
    description="""
## Pesquisa Real em Fontes Brasileiras de Saúde

Esta API realiza pesquisas **reais** em múltiplas fontes de saúde,
retornando artigos verídicos com links funcionais, DOIs reais e abstracts completos.

### Fontes de Dados (19 fontes)

**Bases de Dados Internacionais**
- **PubMed** – NCBI E-utilities API oficial · abstract completo · DOI real · PMID
- **Cochrane Library** – EuropePMC API · revisões sistemáticas e meta-análises
- **SciELO** – search.scielo.org · artigos científicos em português/inglês
- **Semantic Scholar** – Allen AI Graph API · +200 M papers · citationCount · `S2_API_KEY` opcional e gratuita
- **OpenAlex** – OurResearch · +250 M papers · totalmente aberto · sem autenticação
- **Google Scholar (scholarly)** – via `scholarly` + proxy SOCKS5 local · requer `GOOGLE_SCHOLAR_PROXY`
- **Google Scholar (SerpAPI)** – API paga · sem bloqueios · requer `SERPAPI_KEY`
- **Google Scholar (SearchApi.io)** – API paga · sem bloqueios · requer `SEARCHAPI_KEY`
- **Google Scholar (ScholarAPI.net)** – API especializada · requer `SCHOLARAPI_KEY`
- **Google Scholar (Serply.io)** – API confiável · requer `SERPLY_API_KEY`

**Bases de Dados Nacionais / Latino-Americanas**
- **LILACS/BVS** – pesquisa.bvsalud.org · literatura latino-americana (BIREME)
- **Redalyc** – rede de revistas latino-americanas de acesso aberto
- **BDTD** – IBICT/VuFind · teses e dissertações brasileiras
- **Portal CAPES** – CrossRef API · metadados de periódicos indexados pelo CAPES

**Protocolos e Diretrizes Nacionais**
- **Ministério da Saúde** – PCDTs e BVS (gov.br) · protocolos oficiais
- **SBMFC, SBP, SBPT, SBC** – protocolos e diretrizes das sociedades médicas

### Garantias
- **Zero dados fictícios**: nenhum resultado é fabricado — lista vazia se sem resultados
- **Links reais**: todas as URLs apontam para documentos existentes
- **Abstracts completos**: via NCBI E-utilities para PubMed e EuropePMC para Cochrane
- **DOIs verificados**: extraídos dos metadados reais dos artigos
- **Cache inteligente**: curto (5 min) · médio (1 h para buscas) · longo (24 h para PCDTs)

### Autenticação
Envie sua API Key no header `X-API-Key`:

```bash
curl -H "X-API-Key: sk-pesquisa-saude-2026-master-key" \\
  "https://req.joaosmfilho.org/pesquisar?q=diabetes"
```

### Playground
Teste a API diretamente no browser, sem curl ou código:
👉 [/playground](https://req.joaosmfilho.org/playground)

---

## 🎨 Integração com Lovable — Prompt Copia e Cola

Cole o bloco abaixo no [Lovable](https://lovable.dev) para integrar a API ao seu projeto:

```
Adicione integração completa com a API de Pesquisa em Saúde brasileira (v3.0).

## 1. Configuração — .env.local

VITE_API_URL=https://req.joaosmfilho.org
VITE_API_KEY=sk-pesquisa-saude-2026-master-key

# APIs do Google Scholar (opcionais - para redundância)
VITE_SERPAPI_KEY=xxx           # https://serpapi.com/manage-api-key
VITE_SEARCHAPI_KEY=xxx         # https://www.searchapi.io/api-key
VITE_SCHOLARAPI_KEY=xxx        # https://scholarapi.net
VITE_SERPLY_API_KEY=xxx        # https://serply.io

## 2. src/lib/pesquisaSaude.ts

const API_URL = import.meta.env.VITE_API_URL || 'https://req.joaosmfilho.org';
const API_KEY  = import.meta.env.VITE_API_KEY  || 'sk-pesquisa-saude-2026-master-key';

export type FonteSlug =
  | 'pubmed' | 'cochrane' | 'scielo' | 'lilacs' | 'capes' | 'semanticscholar' | 'openalex' | 'googlescholar'
  | 'serpapi' | 'searchapi' | 'scholarapi' | 'serply'
  | 'redalyc' | 'bdtd'
  | 'ministerio' | 'sbmfc' | 'sbp' | 'sbpt' | 'sbc';

export interface ResultadoPesquisa {
  id: string | null; titulo: string; resumo: string | null;
  autores: string[] | null; ano: number | null;
  fonte: string; tipo: string; url: string | null;
  doi: string | null; pmid: string | null;
  journal: string | null; volume: string | null;
  issue: string | null; paginas: string | null;
  citacao_abnt: string | null; referencia_abnt: string | null;
}

export interface PesquisaResponse {
  resultados: ResultadoPesquisa[]; total: number; query: string;
  fontes_consultadas: string[]; referencias_completas: string[];
}

export interface RespostaFormatada {
  texto: string; citacoes_usadas: string[]; referencias: string[];
}

const hdrs = () => ({ 'X-API-Key': API_KEY, 'Content-Type': 'application/json' });

export async function pesquisar(
  query: string,
  { fontes, anoMin = 2016, limit = 50, incluirCitacoes = true }:
  { fontes?: FonteSlug[]; anoMin?: number; limit?: number; incluirCitacoes?: boolean } = {}
): Promise<PesquisaResponse> {
  const res = await fetch(`${API_URL}/pesquisar`, {
    method: 'POST', headers: hdrs(),
    body: JSON.stringify({ query, ano_min: anoMin, limit,
      incluir_citacoes: incluirCitacoes, fontes: fontes ?? null }),
  });
  if (!res.ok) throw new Error(`Erro ${res.status}`);
  return res.json();
}

export async function pesquisarPorFonte(
  fonte: FonteSlug, query: string,
  { anoMin = 2016, limit = 20 }: { anoMin?: number; limit?: number } = {}
): Promise<PesquisaResponse> {
  const p = new URLSearchParams({ q: query, ano_min: String(anoMin), limit: String(limit) });
  const res = await fetch(`${API_URL}/pesquisar/${fonte}?${p}`, { headers: hdrs() });
  if (!res.ok) throw new Error(`Erro ${res.status}`);
  return res.json();
}

export async function obterRespostaFormatada(
  query: string,
  { anoMin = 2016, limit = 20 }: { anoMin?: number; limit?: number } = {}
): Promise<RespostaFormatada> {
  const res = await fetch(`${API_URL}/resposta`, {
    method: 'POST', headers: hdrs(),
    body: JSON.stringify({ query, ano_min: anoMin, limit }),
  });
  if (!res.ok) throw new Error(`Erro ${res.status}`);
  return res.json();
}

export async function verificarStatus() {
  const res = await fetch(`${API_URL}/status`, { headers: hdrs() });
  if (!res.ok) throw new Error('Erro status');
  return res.json();
}

## 3. src/components/PesquisaSaude.tsx

import { useState } from 'react';
import { pesquisar, type ResultadoPesquisa, type FonteSlug } from '@/lib/pesquisaSaude';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Loader2, Search, ExternalLink, Copy, CheckCheck } from 'lucide-react';

const FONTES: { slug: FonteSlug; label: string }[] = [
  { slug: 'pubmed',     label: 'PubMed'            },
  { slug: 'cochrane',   label: 'Cochrane'           },
  { slug: 'scielo',     label: 'SciELO'             },
  { slug: 'lilacs',     label: 'LILACS/BVS'         },
  { slug: 'capes',      label: 'Portal CAPES'       },
  { slug: 'semanticscholar', label: 'Semantic Scholar'   },
  { slug: 'openalex',       label: 'OpenAlex'           },
  { slug: 'googlescholar',  label: 'Google Scholar (proxy)'     },
  { slug: 'serpapi',    label: 'Google Scholar (SerpAPI)'     },
  { slug: 'searchapi',  label: 'Google Scholar (SearchApi)'   },
  { slug: 'scholarapi', label: 'Google Scholar (ScholarAPI)'  },
  { slug: 'serply',     label: 'Google Scholar (Serply)'      },
  { slug: 'redalyc',    label: 'Redalyc'            },
  { slug: 'bdtd',       label: 'BDTD (Teses)'       },
  { slug: 'ministerio', label: 'Min. Saúde (PCDT)'  },
  { slug: 'sbmfc',      label: 'SBMFC'              },
  { slug: 'sbp',        label: 'SBP'                },
  { slug: 'sbpt',       label: 'SBPT'               },
  { slug: 'sbc',        label: 'SBC'                },
];

export function PesquisaSaude() {
  const [termo, setTermo]           = useState('');
  const [fontesSel, setFontesSel]   = useState<FonteSlug[]>([]);
  const [resultados, setResultados] = useState<ResultadoPesquisa[]>([]);
  const [referencias, setRefs]      = useState<string[]>([]);
  const [fontesCons, setFontesCons] = useState<string[]>([]);
  const [loading, setLoading]       = useState(false);
  const [erro, setErro]             = useState<string | null>(null);
  const [copiado, setCopiado]       = useState<string | null>(null);

  const toggleFonte = (slug: FonteSlug) =>
    setFontesSel(p => p.includes(slug) ? p.filter(f => f !== slug) : [...p, slug]);

  const copiar = (txt: string, id: string) =>
    navigator.clipboard.writeText(txt).then(() => {
      setCopiado(id); setTimeout(() => setCopiado(null), 1800);
    });

  const handlePesquisar = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!termo.trim()) return;
    setLoading(true); setErro(null);
    try {
      const d = await pesquisar(termo, { fontes: fontesSel.length ? fontesSel : undefined, limit: 30 });
      setResultados(d.resultados); setRefs(d.referencias_completas); setFontesCons(d.fontes_consultadas);
    } catch (err: any) {
      setErro(err.message ?? 'Erro ao pesquisar.');
    } finally { setLoading(false); }
  };

  return (
    <div className="w-full max-w-4xl mx-auto space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2"><Search className="w-5 h-5"/>Pesquisa em Saúde</CardTitle>
          <CardDescription>8 fontes brasileiras · dados reais · citações ABNT automáticas</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex flex-wrap gap-2">
            {FONTES.map(f => (
              <button key={f.slug} type="button" onClick={() => toggleFonte(f.slug)}
                className={`px-3 py-1 rounded-full text-xs font-semibold border transition-colors ${
                  fontesSel.includes(f.slug)
                    ? 'bg-primary text-primary-foreground border-primary'
                    : 'bg-background text-muted-foreground border-border hover:border-primary'}`}>
                {f.label}
              </button>
            ))}
          </div>
          <form onSubmit={handlePesquisar} className="flex gap-2">
            <Input placeholder="Ex: diabetes, hipertensão gestante, DPOC..." value={termo}
              onChange={e => setTermo(e.target.value)} className="flex-1"/>
            <Button type="submit" disabled={loading}>
              {loading ? <Loader2 className="w-4 h-4 animate-spin"/> : <Search className="w-4 h-4"/>}
              Pesquisar
            </Button>
          </form>
          {erro && <div className="bg-destructive/10 text-destructive p-3 rounded-md text-sm">{erro}</div>}
          {fontesCons.length > 0 && (
            <p className="text-xs text-muted-foreground">{resultados.length} resultado(s) · {fontesCons.join(', ')}</p>
          )}
        </CardContent>
      </Card>

      {resultados.map((item, i) => (
        <Card key={item.url ?? item.doi ?? i}>
          <CardHeader className="pb-2">
            <CardTitle className="text-base">
              {item.url
                ? <a href={item.url} target="_blank" rel="noopener noreferrer"
                    className="hover:underline flex items-start gap-1">
                    {item.titulo}<ExternalLink className="w-3 h-3 mt-1 shrink-0 opacity-60"/>
                  </a>
                : item.titulo}
            </CardTitle>
            <CardDescription className="flex flex-wrap gap-2 mt-1">
              <Badge variant="secondary">{item.fonte}</Badge>
              {item.ano && <span>{item.ano}</span>}
              {item.doi && <span className="text-xs opacity-60">DOI: {item.doi}</span>}
              {item.pmid && <span className="text-xs opacity-60">PMID: {item.pmid}</span>}
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-2">
            {item.autores && item.autores.length > 0 && (
              <p className="text-xs text-muted-foreground">
                {item.autores.slice(0,4).join('; ')}{item.autores.length > 4 ? ' et al.' : ''}
              </p>
            )}
            {item.resumo && <p className="text-sm text-muted-foreground line-clamp-3">{item.resumo}</p>}
            {item.referencia_abnt && (
              <div className="flex items-start gap-2 bg-muted/50 rounded p-2">
                <code className="text-xs flex-1 break-words">{item.referencia_abnt}</code>
                <button type="button" onClick={() => copiar(item.referencia_abnt!, `ref-${i}`)}
                  className="shrink-0 text-muted-foreground hover:text-primary" title="Copiar referência ABNT">
                  {copiado === `ref-${i}` ? <CheckCheck className="w-4 h-4 text-green-500"/> : <Copy className="w-4 h-4"/>}
                </button>
              </div>
            )}
          </CardContent>
        </Card>
      ))}

      {!loading && resultados.length === 0 && termo && !erro && (
        <p className="text-center text-muted-foreground py-8">
          Nenhum resultado para "{termo}". Tente outro termo ou selecione mais fontes.
        </p>
      )}

      {referencias.length > 0 && (
        <Card>
          <CardHeader><CardTitle className="text-sm">Referências Bibliográficas (ABNT)</CardTitle></CardHeader>
          <CardContent>
            <ol className="space-y-2">
              {referencias.map((ref, i) => (
                <li key={i} className="text-xs text-muted-foreground flex gap-2">
                  <span className="shrink-0 font-semibold">{i+1}.</span><span>{ref}</span>
                </li>
              ))}
            </ol>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

## 4. src/pages/Index.tsx

import { PesquisaSaude } from '@/components/PesquisaSaude';

export default function Index() {
  return (
    <div className="container py-8">
      <h1 className="text-2xl font-bold mb-6">Pesquisa em Saúde</h1>
      <PesquisaSaude />
    </div>
  );
}

## Endpoints

Base URL: https://req.joaosmfilho.org  |  Auth: header X-API-Key

POST /pesquisar          → busca avançada (body JSON com query, fontes, ano_min, limit)
GET  /pesquisar?q=termo  → busca simples via query string
GET  /pesquisar/{fonte}  → busca em fonte específica (19 fontes disponíveis)
POST /resposta           → texto formatado com citações ABNT embutidas
GET  /fontes             → lista as 19 fontes disponíveis
GET  /status             → status operacional de cada fonte
GET  /playground         → interface visual para testar sem código
GET  /docs               → Swagger UI

### Fontes Disponíveis (19)

**Google Scholar (5 opções):**
- `googlescholar` - Google Scholar via proxy SOCKS5 (requer GOOGLE_SCHOLAR_PROXY)
- `serpapi` - Google Scholar via SerpAPI (requer SERPAPI_KEY)
- `searchapi` - Google Scholar via SearchApi.io (requer SEARCHAPI_KEY)
- `scholarapi` - Google Scholar via ScholarAPI.net (requer SCHOLARAPI_KEY)
- `serply` - Google Scholar via Serply.io (requer SERPLY_API_KEY)

**Bases Internacionais:** pubmed, cochrane, scielo, semanticscholar, openalex

**Bases Nacionais/Latino-Americanas:** lilacs, redalyc, bdtd, capes

**Protocolos Nacionais:** ministerio, sbmfc, sbp, sbpt, sbc
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
            "playground": "/playground",
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

# ─── HTML do Playground ─────────────────────────────────────────────────────

_PLAYGROUND_HTML = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>Playground – API Pesquisa Saúde</title>
<style>
  :root {
    --bg: #0f172a;
    --surface: #1e293b;
    --surface2: #273549;
    --border: #334155;
    --accent: #38bdf8;
    --accent-dark: #0ea5e9;
    --text: #e2e8f0;
    --text-muted: #94a3b8;
    --green: #4ade80;
    --red: #f87171;
    --yellow: #fbbf24;
    --radius: 10px;
    --shadow: 0 4px 24px rgba(0,0,0,.4);
  }
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    font-family: 'Segoe UI', system-ui, sans-serif;
    background: var(--bg);
    color: var(--text);
    min-height: 100vh;
    padding: 24px 16px;
  }
  a { color: var(--accent); text-decoration: none; }
  a:hover { text-decoration: underline; }
  h1 { font-size: 1.6rem; font-weight: 700; margin-bottom: 4px; }
  .subtitle { color: var(--text-muted); font-size: .9rem; margin-bottom: 24px; }
  .badge {
    display: inline-block; font-size: .7rem; font-weight: 600;
    padding: 2px 8px; border-radius: 999px; margin-left: 8px;
    background: var(--accent); color: #0f172a; vertical-align: middle;
  }
  /* Layout */
  .layout { display: grid; grid-template-columns: 340px 1fr; gap: 20px; max-width: 1200px; margin: 0 auto; }
  @media (max-width: 860px) { .layout { grid-template-columns: 1fr; } }
  /* Panel */
  .panel {
    background: var(--surface); border: 1px solid var(--border);
    border-radius: var(--radius); padding: 20px; box-shadow: var(--shadow);
  }
  .panel-title { font-size: .8rem; font-weight: 700; text-transform: uppercase;
    letter-spacing: .08em; color: var(--text-muted); margin-bottom: 16px; }
  /* Form */
  .field { margin-bottom: 14px; }
  label { display: block; font-size: .8rem; color: var(--text-muted);
    margin-bottom: 4px; font-weight: 600; }
  input[type=text], input[type=number], input[type=password] {
    width: 100%; padding: 9px 12px; border-radius: 6px;
    border: 1px solid var(--border); background: var(--bg);
    color: var(--text); font-size: .9rem; outline: none;
    transition: border-color .15s;
  }
  input:focus { border-color: var(--accent); }
  /* Fontes checkboxes */
  .sources-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 6px; }
  .source-check { display: flex; align-items: center; gap: 6px; font-size: .82rem;
    padding: 5px 8px; border-radius: 5px; border: 1px solid var(--border);
    background: var(--bg); cursor: pointer; user-select: none; transition: border-color .15s; }
  .source-check:hover { border-color: var(--accent); }
  .source-check input { width: 14px; height: 14px; accent-color: var(--accent); cursor: pointer; }
  .type-badge { font-size: .65rem; padding: 1px 5px; border-radius: 999px;
    font-weight: 700; margin-left: auto; }
  .type-governo  { background: #166534; color: #bbf7d0; }
  .type-sociedade { background: #1d4ed8; color: #bfdbfe; }
  .type-base_dados { background: #6d28d9; color: #ddd6fe; }
  /* Inline row */
  .row { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
  /* Button */
  .btn {
    width: 100%; padding: 11px; border-radius: 7px; border: none;
    font-size: .95rem; font-weight: 700; cursor: pointer;
    background: var(--accent-dark); color: #fff;
    transition: background .15s, transform .1s;
    display: flex; align-items: center; justify-content: center; gap: 8px;
  }
  .btn:hover { background: var(--accent); }
  .btn:active { transform: scale(.98); }
  .btn:disabled { opacity: .5; cursor: not-allowed; }
  /* Status bar */
  #status-bar {
    font-size: .82rem; padding: 8px 12px; border-radius: 6px;
    margin-top: 12px; display: none;
    align-items: center; gap: 8px;
  }
  #status-bar.loading { display: flex; background: #1c3b5a; color: var(--accent); }
  #status-bar.error   { display: flex; background: #3b1c1c; color: var(--red); }
  #status-bar.success { display: flex; background: #1c3b26; color: var(--green); }
  .spinner { width: 16px; height: 16px; border: 2px solid currentColor;
    border-top-color: transparent; border-radius: 50%; animation: spin .6s linear infinite; }
  @keyframes spin { to { transform: rotate(360deg); } }
  /* Results panel header */
  .results-header { display: flex; align-items: center; justify-content: space-between;
    margin-bottom: 16px; }
  #results-count { font-size: .82rem; color: var(--text-muted); }
  #results-time  { font-size: .75rem; color: var(--text-muted); }
  /* Cards */
  #results-list { display: flex; flex-direction: column; gap: 14px; }
  .card {
    background: var(--surface2); border: 1px solid var(--border);
    border-radius: var(--radius); padding: 16px 18px;
    animation: fadeIn .2s ease-out;
  }
  @keyframes fadeIn { from { opacity:0; transform:translateY(6px); } to { opacity:1; transform:none; } }
  .card-header { display: flex; gap: 10px; margin-bottom: 8px; align-items: flex-start; }
  .card-index { font-size: .75rem; color: var(--text-muted); min-width: 22px; margin-top: 2px; }
  .card-title { font-size: .95rem; font-weight: 600; line-height: 1.35; }
  .card-title a:hover { color: var(--accent); }
  .meta { display: flex; flex-wrap: wrap; gap: 6px; margin: 8px 0; }
  .meta-chip {
    font-size: .72rem; padding: 2px 8px; border-radius: 999px;
    border: 1px solid var(--border); color: var(--text-muted);
  }
  .meta-chip.fonte  { border-color: var(--accent); color: var(--accent); }
  .meta-chip.doi    { border-color: var(--yellow); color: var(--yellow); }
  .meta-chip.pubmed { border-color: var(--green); color: var(--green); }
  .abstract {
    font-size: .82rem; color: var(--text-muted); line-height: 1.55;
    max-height: 96px; overflow: hidden; position: relative;
    cursor: pointer; transition: max-height .3s;
  }
  .abstract.expanded { max-height: none; }
  .abstract::after {
    content: ''; position: absolute; bottom: 0; left: 0; right: 0;
    height: 32px;
    background: linear-gradient(transparent, var(--surface2));
    pointer-events: none;
  }
  .abstract.expanded::after { display: none; }
  .abnt {
    margin-top: 10px; font-size: .75rem; color: var(--text-muted);
    background: var(--bg); border-left: 3px solid var(--border);
    padding: 6px 10px; border-radius: 0 5px 5px 0;
    cursor: pointer; position: relative;
  }
  .abnt:hover { border-left-color: var(--accent); }
  .copy-tip {
    position: absolute; right: 8px; top: 50%; transform: translateY(-50%);
    font-size: .68rem; color: var(--text-muted); opacity: 0; transition: opacity .15s;
  }
  .abnt:hover .copy-tip { opacity: 1; }
  /* Placeholder */
  #placeholder {
    text-align: center; padding: 60px 20px; color: var(--text-muted);
  }
  #placeholder svg { margin-bottom: 16px; opacity: .3; }
  /* References section */
  #refs-section { margin-top: 20px; display: none; }
  #refs-section summary {
    cursor: pointer; font-size: .8rem; font-weight: 700;
    color: var(--text-muted); padding: 10px 14px;
    background: var(--surface); border: 1px solid var(--border);
    border-radius: var(--radius); user-select: none;
  }
  #refs-list {
    background: var(--surface); border: 1px solid var(--border);
    border-top: none; border-radius: 0 0 var(--radius) var(--radius);
    padding: 14px; font-size: .78rem; color: var(--text-muted);
    line-height: 1.7; max-height: 300px; overflow-y: auto;
  }
  #refs-list p { margin-bottom: 8px; }
  /* Toast */
  #toast {
    position: fixed; bottom: 24px; right: 24px; padding: 8px 16px;
    background: var(--accent-dark); color: #fff; border-radius: 7px;
    font-size: .82rem; font-weight: 600; opacity: 0;
    transition: opacity .2s; pointer-events: none; z-index: 999;
  }
  #toast.show { opacity: 1; }
</style>
</head>
<body>
<div style="max-width:1200px;margin:0 auto 20px;">
  <h1>🔬 API Pesquisa Saúde <span class="badge">v3.0</span></h1>
  <p class="subtitle">
    Playground interativo — teste em tempo real as buscas em 15 fontes de saúde (nacionais e internacionais).
    Resultados reais · Links verificados · Abstracts completos · Citações ABNT
    &nbsp;·&nbsp; <a href="/docs" target="_blank">Swagger UI</a>
  </p>
</div>

<div class="layout">
  <!-- Painel de Controle -->
  <aside class="panel">
    <p class="panel-title">⚙️ Parâmetros da Busca</p>

    <div class="field">
      <label for="api-key">🔑 API Key</label>
      <input type="password" id="api-key" value="sk-pesquisa-saude-2026-master-key"
        placeholder="sk-pesquisa-saude-..." autocomplete="off" />
    </div>

    <div class="field">
      <label for="query">🔍 Termo de busca</label>
      <input type="text" id="query" placeholder="ex: diabetes, hipertensão, DPOC…"
        value="" autocomplete="off" />
    </div>

    <div class="field">
      <label>📚 Fontes</label>
      <div class="sources-grid" id="sources-grid"></div>
      <div style="display:flex;gap:8px;margin-top:8px;">
        <button onclick="toggleAll(true)"  style="flex:1;font-size:.75rem;padding:4px;border-radius:5px;border:1px solid var(--border);background:var(--bg);color:var(--text-muted);cursor:pointer;">Todas</button>
        <button onclick="toggleAll(false)" style="flex:1;font-size:.75rem;padding:4px;border-radius:5px;border:1px solid var(--border);background:var(--bg);color:var(--text-muted);cursor:pointer;">Nenhuma</button>
      </div>
    </div>

    <div class="row">
      <div class="field">
        <label for="ano-min">📅 Ano mínimo</label>
        <input type="number" id="ano-min" value="2016" min="1990" max="2026" />
      </div>
      <div class="field">
        <label for="limit">📊 Limite</label>
        <input type="number" id="limit" value="20" min="1" max="100" />
      </div>
    </div>

    <button class="btn" id="search-btn" onclick="buscar()">
      <span>🚀</span><span>Pesquisar</span>
    </button>

    <div id="status-bar">
      <div class="spinner" id="spinner" style="display:none;"></div>
      <span id="status-text"></span>
    </div>

    <div style="margin-top:20px;border-top:1px solid var(--border);padding-top:14px;">
      <p class="panel-title">ℹ️ Exemplos rápidos</p>
      <div style="display:flex;flex-direction:column;gap:6px;">
        <button class="quick-btn" onclick="setQuery('diabetes tipo 2')">diabetes tipo 2</button>
        <button class="quick-btn" onclick="setQuery('hipertensão arterial gestação')">hipertensão arterial gestação</button>
        <button class="quick-btn" onclick="setQuery('DPOC tratamento')">DPOC tratamento</button>
        <button class="quick-btn" onclick="setQuery('amamentação aleitamento')">amamentação aleitamento</button>
        <button class="quick-btn" onclick="setQuery('depressão antidepressivo')">depressão antidepressivo</button>
      </div>
    </div>
  </aside>

  <!-- Painel de Resultados -->
  <section class="panel" style="overflow:hidden;">
    <div class="results-header">
      <p class="panel-title" style="margin-bottom:0;">📄 Resultados</p>
      <div>
        <span id="results-count"></span>
        <span id="results-time" style="margin-left:12px;"></span>
      </div>
    </div>

    <div id="results-list">
      <div id="placeholder">
        <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
          <circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/>
        </svg>
        <p style="font-size:1rem;font-weight:600;margin-bottom:6px;">Pronto para pesquisar</p>
        <p style="font-size:.85rem;">Digite um termo e clique em Pesquisar</p>
      </div>
    </div>

    <details id="refs-section">
      <summary id="refs-summary">📋 Referências Completas (ABNT)</summary>
      <div id="refs-list"></div>
    </details>
  </section>
</div>

<div id="toast"></div>

<style>
  .quick-btn {
    text-align:left; padding:6px 10px; border-radius:6px; border:1px solid var(--border);
    background:var(--bg); color:var(--text-muted); cursor:pointer; font-size:.78rem;
    transition:border-color .15s,color .15s;
  }
  .quick-btn:hover { border-color:var(--accent); color:var(--text); }
</style>

<script>
  const FONTES = [
    { slug: "pubmed",    label: "PubMed",             tipo: "base_dados" },
    { slug: "cochrane",  label: "Cochrane",            tipo: "base_dados" },
    { slug: "scielo",    label: "SciELO",              tipo: "base_dados" },
    { slug: "lilacs",    label: "LILACS/BVS",          tipo: "base_dados" },
    { slug: "capes",           label: "Portal CAPES",        tipo: "base_dados" },
    { slug: "semanticscholar", label: "Semantic Scholar",    tipo: "base_dados" },
    { slug: "openalex",        label: "OpenAlex",            tipo: "base_dados" },
    { slug: "googlescholar",   label: "Google Scholar",      tipo: "base_dados" },
    { slug: "redalyc",         label: "Redalyc",             tipo: "base_dados" },
    { slug: "bdtd",      label: "BDTD (Teses)",        tipo: "base_dados" },
    { slug: "ministerio",label: "Ministério Saúde",    tipo: "governo"    },
    { slug: "sbmfc",     label: "SBMFC",               tipo: "sociedade"  },
    { slug: "sbp",       label: "SBP",                 tipo: "sociedade"  },
    { slug: "sbpt",      label: "SBPT",                tipo: "sociedade"  },
    { slug: "sbc",       label: "SBC",                 tipo: "sociedade"  },
  ];

  const TYPE_BADGE = {
    governo:    ["type-governo",    "GOV"],
    sociedade:  ["type-sociedade",  "SOC"],
    base_dados: ["type-base_dados", "DB"],
  };

  // Build checkboxes
  const grid = document.getElementById("sources-grid");
  FONTES.forEach(f => {
    const lbl = document.createElement("label");
    lbl.className = "source-check";
    lbl.title = f.slug;
    const [cls, txt] = TYPE_BADGE[f.tipo] || ["", ""];
    lbl.innerHTML = `<input type="checkbox" value="${f.slug}" checked />${f.label}<span class="type-badge ${cls}">${txt}</span>`;
    grid.appendChild(lbl);
  });

  function toggleAll(on) {
    document.querySelectorAll("#sources-grid input[type=checkbox]").forEach(c => c.checked = on);
  }

  function setQuery(q) {
    document.getElementById("query").value = q;
    buscar();
  }

  function showStatus(type, msg) {
    const bar = document.getElementById("status-bar");
    bar.className = type;
    document.getElementById("status-text").textContent = msg;
    document.getElementById("spinner").style.display = type === "loading" ? "block" : "none";
  }

  function toast(msg) {
    const el = document.getElementById("toast");
    el.textContent = msg;
    el.classList.add("show");
    setTimeout(() => el.classList.remove("show"), 1800);
  }

  function copyText(text) {
    navigator.clipboard.writeText(text).then(() => toast("Copiado!")).catch(() => {});
  }

  function toggleAbstract(el) {
    el.classList.toggle("expanded");
  }

  async function buscar() {
    const q       = document.getElementById("query").value.trim();
    const apiKey  = document.getElementById("api-key").value.trim();
    const anoMin  = parseInt(document.getElementById("ano-min").value) || 2016;
    const limit   = parseInt(document.getElementById("limit").value)   || 20;
    const checked = [...document.querySelectorAll("#sources-grid input:checked")].map(c => c.value);

    if (!q) { showStatus("error", "Digite um termo de busca!"); return; }
    if (!apiKey) { showStatus("error", "API Key obrigatória!"); return; }
    if (checked.length === 0) { showStatus("error", "Selecione ao menos uma fonte!"); return; }

    const btn = document.getElementById("search-btn");
    btn.disabled = true;
    showStatus("loading", "Buscando em " + checked.length + " fonte(s)…");
    document.getElementById("results-list").innerHTML = "";
    document.getElementById("results-count").textContent = "";
    document.getElementById("results-time").textContent = "";
    document.getElementById("refs-section").style.display = "none";

    const t0 = Date.now();

    try {
      const body = { query: q, ano_min: anoMin, limit, incluir_citacoes: true, fontes: checked };
      const resp = await fetch("/pesquisar", {
        method: "POST",
        headers: { "Content-Type": "application/json", "X-API-Key": apiKey },
        body: JSON.stringify(body),
      });

      const elapsed = ((Date.now() - t0) / 1000).toFixed(2);

      if (!resp.ok) {
        const err = await resp.json().catch(() => ({ detail: "Erro desconhecido" }));
        showStatus("error", "Erro " + resp.status + ": " + (err.detail || resp.statusText));
        return;
      }

      const data = await resp.json();
      const { resultados, total, fontes_consultadas, referencias_completas } = data;

      document.getElementById("results-count").textContent =
        total + " resultado" + (total !== 1 ? "s" : "") +
        (fontes_consultadas.length ? " · " + fontes_consultadas.join(", ") : "");
      document.getElementById("results-time").textContent = elapsed + "s";

      if (total === 0) {
        showStatus("error", "Nenhum resultado encontrado. Tente outro termo ou mais fontes.");
        document.getElementById("results-list").innerHTML =
          '<div id="placeholder"><p style="font-size:.9rem;color:var(--text-muted)">Nenhum resultado. Tente ampliar o período, mudar o termo ou selecionar mais fontes.</p></div>';
        return;
      }

      showStatus("success", "✓ " + total + " resultado(s) encontrado(s) em " + elapsed + "s");

      const list = document.getElementById("results-list");
      resultados.forEach((art, i) => {
        const card = document.createElement("div");
        card.className = "card";

        const titleHtml = art.url
          ? `<a href="${esc(art.url)}" target="_blank" rel="noopener">${esc(art.titulo)}</a>`
          : esc(art.titulo);

        const authorsHtml = art.autores && art.autores.length
          ? art.autores.slice(0, 3).map(a => esc(a)).join("; ") + (art.autores.length > 3 ? " et al." : "")
          : "";

        const chips = [];
        if (art.fonte)   chips.push(`<span class="meta-chip fonte">${esc(art.fonte)}</span>`);
        if (art.ano)     chips.push(`<span class="meta-chip">${art.ano}</span>`);
        if (art.tipo)    chips.push(`<span class="meta-chip">${esc(art.tipo)}</span>`);
        if (art.doi)     chips.push(`<span class="meta-chip doi" title="DOI: ${esc(art.doi)}">DOI</span>`);
        if (art.pmid)    chips.push(`<span class="meta-chip pubmed">PMID ${esc(art.pmid)}</span>`);
        if (art.journal) chips.push(`<span class="meta-chip" style="max-width:180px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;" title="${esc(art.journal)}">${esc(art.journal)}</span>`);

        const abstractHtml = art.resumo
          ? `<div class="abstract" onclick="toggleAbstract(this)" title="Clique para expandir">${esc(art.resumo)}</div>`
          : "";

        const keywordsHtml = art.keywords && art.keywords.length
          ? `<div style="font-size:.72rem;color:var(--text-muted);margin-top:6px;">🏷️ ${art.keywords.map(k => esc(k)).join(" · ")}</div>`
          : "";

        const abntHtml = art.referencia_abnt
          ? `<div class="abnt" onclick="copyText(${JSON.stringify(art.referencia_abnt)})" title="Clique para copiar">
               <span style="font-weight:600;color:var(--yellow);">${esc(art.citacao_abnt || "")}</span>
               &nbsp;${esc(art.referencia_abnt)}
               <span class="copy-tip">📋 copiar</span>
             </div>`
          : "";

        card.innerHTML = `
          <div class="card-header">
            <span class="card-index">${i + 1}.</span>
            <span class="card-title">${titleHtml}</span>
          </div>
          ${authorsHtml ? `<div style="font-size:.78rem;color:var(--text-muted);margin-bottom:6px;">${authorsHtml}</div>` : ""}
          <div class="meta">${chips.join("")}</div>
          ${abstractHtml}
          ${keywordsHtml}
          ${abntHtml}
        `;
        list.appendChild(card);
      });

      // References section
      if (referencias_completas && referencias_completas.length > 0) {
        const sec = document.getElementById("refs-section");
        const refList = document.getElementById("refs-list");
        document.getElementById("refs-summary").textContent =
          `📋 Referências Completas ABNT (${referencias_completas.length})`;
        refList.innerHTML = referencias_completas
          .map((r, i) => `<p><strong>${i+1}.</strong> ${esc(r)}</p>`)
          .join("");
        sec.style.display = "block";
      }

    } catch (e) {
      showStatus("error", "Erro de rede: " + e.message);
    } finally {
      btn.disabled = false;
    }
  }

  function esc(str) {
    if (!str) return "";
    return String(str)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  // Search on Enter key in query input
  document.getElementById("query").addEventListener("keydown", e => {
    if (e.key === "Enter") buscar();
  });
</script>
</body>
</html>"""


@app.get("/playground", response_class=HTMLResponse, tags=["Playground"], include_in_schema=True)
async def playground():
    """
    **Playground interativo** para testar a API em tempo real diretamente no browser.

    - Formulário com todos os parâmetros (query, fontes, ano mínimo, limite, API Key)
    - Resultados reais: título clicável, autores, DOI, abstract, citação ABNT
    - Copia referências ABNT com um clique
    - Sem necessidade de curl ou código

    Abra em: `/playground`
    """
    return HTMLResponse(content=_PLAYGROUND_HTML)

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
    Pesquisa unificada em TODAS as fontes de saúde (15 fontes).

    Retorna artigos **reais** com:
    - Links funcionais para os documentos originais
    - DOIs verificados
    - Abstracts completos (PubMed via NCBI E-utilities; Cochrane via EuropePMC)
    - Citações ABNT automáticas

    **Fontes disponíveis:** ministerio, sbmfc, sbp, sbpt, sbc, scielo, lilacs, pubmed,
    cochrane, redalyc, bdtd, capes, semanticscholar, openalex, googlescholar

    **Exemplo:**
    ```bash
    curl -H "X-API-Key: sk-key" "https://req.joaosmfilho.org/pesquisar?q=diabetes&fontes=pubmed,cochrane,scielo&limit=20"
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
    fonte: str = Path(..., description="Slug da fonte: ministerio, sbmfc, sbp, sbpt, sbc, scielo, lilacs, pubmed, cochrane, redalyc, bdtd, capes, semanticscholar, openalex, googlescholar"),
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
            keywords=r.get("keywords") or None,
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
