# Integração com Projetos Lovable — API de Pesquisa em Saúde v3.0

Prompt **copia e cola** para integrar a API de Pesquisa em Saúde brasileira em projetos criados com [Lovable](https://lovable.dev).

> **Novidades v3.0:** busca real (zero dados fictícios), `/pesquisar/{fonte}`, `/status`, `/playground`, cache TTL, NCBI E-utilities para PubMed, LILACS via BVS.

---

## 📋 Prompt para Lovable — Copia e Cola

```
Adicione integração completa com a API de Pesquisa em Saúde brasileira (v3.0).

## 1. Configuração do ambiente

Crie `.env.local` (substitua a API Key pela sua chave de produção antes de publicar):

VITE_API_URL=https://req.joaosmfilho.org
VITE_API_KEY=sk-pesquisa-saude-2026-master-key

## 2. Biblioteca cliente — src/lib/pesquisaSaude.ts

const API_URL = import.meta.env.VITE_API_URL || 'https://req.joaosmfilho.org';
const API_KEY  = import.meta.env.VITE_API_KEY  || 'sk-pesquisa-saude-2026-master-key';

export type FonteSlug =
  | 'pubmed' | 'scielo' | 'lilacs' | 'ministerio'
  | 'sbmfc'  | 'sbp'   | 'sbpt'   | 'sbc';

export interface ResultadoPesquisa {
  id:               string | null;
  titulo:           string;
  resumo:           string | null;
  autores:          string[] | null;
  ano:              number | null;
  fonte:            string;
  tipo:             string;
  url:              string | null;
  doi:              string | null;
  pmid:             string | null;
  journal:          string | null;
  volume:           string | null;
  issue:            string | null;
  paginas:          string | null;
  citacao_abnt:     string | null;
  referencia_abnt:  string | null;
}

export interface PesquisaResponse {
  resultados:           ResultadoPesquisa[];
  total:                number;
  query:                string;
  fontes_consultadas:   string[];
  referencias_completas: string[];
}

export interface RespostaFormatada {
  texto:          string;
  citacoes_usadas: string[];
  referencias:    string[];
}

const headers = () => ({
  'X-API-Key':    API_KEY,
  'Content-Type': 'application/json',
});

/** Pesquisa em múltiplas fontes simultaneamente */
export async function pesquisar(
  query: string,
  {
    fontes,
    anoMin = 2016,
    limit  = 50,
    incluirCitacoes = true,
  }: {
    fontes?: FonteSlug[];
    anoMin?: number;
    limit?: number;
    incluirCitacoes?: boolean;
  } = {}
): Promise<PesquisaResponse> {
  const res = await fetch(`${API_URL}/pesquisar`, {
    method:  'POST',
    headers: headers(),
    body:    JSON.stringify({
      query,
      ano_min:          anoMin,
      limit,
      incluir_citacoes: incluirCitacoes,
      fontes:           fontes ?? null,
    }),
  });
  if (!res.ok) throw new Error(`Erro ${res.status}: ${await res.text()}`);
  return res.json();
}

/** Pesquisa em uma única fonte (mais rápido) */
export async function pesquisarPorFonte(
  fonte: FonteSlug,
  query: string,
  { anoMin = 2016, limit = 20 }: { anoMin?: number; limit?: number } = {}
): Promise<PesquisaResponse> {
  const params = new URLSearchParams({ q: query, ano_min: String(anoMin), limit: String(limit) });
  const res = await fetch(`${API_URL}/pesquisar/${fonte}?${params}`, { headers: headers() });
  if (!res.ok) throw new Error(`Erro ${res.status}: ${await res.text()}`);
  return res.json();
}

/** Texto com citações ABNT embutidas em cada parágrafo */
export async function obterRespostaFormatada(
  query: string,
  { anoMin = 2016, limit = 20 }: { anoMin?: number; limit?: number } = {}
): Promise<RespostaFormatada> {
  const res = await fetch(`${API_URL}/resposta`, {
    method:  'POST',
    headers: headers(),
    body:    JSON.stringify({ query, ano_min: anoMin, limit }),
  });
  if (!res.ok) throw new Error(`Erro ${res.status}: ${await res.text()}`);
  return res.json();
}

/** Status da API e de cada fonte */
export async function verificarStatus() {
  const res = await fetch(`${API_URL}/status`, { headers: headers() });
  if (!res.ok) throw new Error('Erro ao verificar status');
  return res.json();
}

## 3. Componente de Pesquisa — src/components/PesquisaSaude.tsx

import { useState } from 'react';
import {
  pesquisar, obterRespostaFormatada,
  type ResultadoPesquisa, type FonteSlug,
} from '@/lib/pesquisaSaude';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button }   from '@/components/ui/button';
import { Input }    from '@/components/ui/input';
import { Badge }    from '@/components/ui/badge';
import { Loader2, Search, ExternalLink, Copy, CheckCheck } from 'lucide-react';

const FONTES: { slug: FonteSlug; label: string; tipo: string }[] = [
  { slug: 'pubmed',     label: 'PubMed',          tipo: 'base_dados' },
  { slug: 'scielo',     label: 'SciELO',           tipo: 'base_dados' },
  { slug: 'lilacs',     label: 'LILACS/BVS',       tipo: 'base_dados' },
  { slug: 'ministerio', label: 'Min. Saúde (PCDT)', tipo: 'governo'    },
  { slug: 'sbmfc',      label: 'SBMFC',            tipo: 'sociedade'  },
  { slug: 'sbp',        label: 'SBP',              tipo: 'sociedade'  },
  { slug: 'sbpt',       label: 'SBPT',             tipo: 'sociedade'  },
  { slug: 'sbc',        label: 'SBC',              tipo: 'sociedade'  },
];

export function PesquisaSaude() {
  const [termo, setTermo]               = useState('');
  const [fontesSel, setFontesSel]       = useState<FonteSlug[]>([]);
  const [resultados, setResultados]     = useState<ResultadoPesquisa[]>([]);
  const [referencias, setReferencias]   = useState<string[]>([]);
  const [fontesCons, setFontesCons]     = useState<string[]>([]);
  const [loading, setLoading]           = useState(false);
  const [erro, setErro]                 = useState<string | null>(null);
  const [copiado, setCopiado]           = useState<string | null>(null);

  const toggleFonte = (slug: FonteSlug) =>
    setFontesSel(prev =>
      prev.includes(slug) ? prev.filter(f => f !== slug) : [...prev, slug]
    );

  const copiar = (texto: string, id: string) => {
    navigator.clipboard.writeText(texto).then(() => {
      setCopiado(id);
      setTimeout(() => setCopiado(null), 1800);
    });
  };

  const handlePesquisar = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!termo.trim()) return;
    setLoading(true);
    setErro(null);
    try {
      const dados = await pesquisar(termo, {
        fontes: fontesSel.length > 0 ? fontesSel : undefined,
        limit: 30,
      });
      setResultados(dados.resultados);
      setReferencias(dados.referencias_completas);
      setFontesCons(dados.fontes_consultadas);
    } catch (err: any) {
      setErro(err.message ?? 'Erro ao pesquisar. Tente novamente.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="w-full max-w-4xl mx-auto space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Search className="w-5 h-5" />
            Pesquisa em Saúde
          </CardTitle>
          <CardDescription>
            Busque em 8 fontes brasileiras: Ministério da Saúde, PubMed, SciELO, LILACS, SBMFC, SBP, SBPT, SBC.
            Dados reais · Links verificados · Citações ABNT automáticas.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Seleção de fontes */}
          <div>
            <p className="text-sm font-medium mb-2 text-muted-foreground">
              Fontes (vazio = todas):
            </p>
            <div className="flex flex-wrap gap-2">
              {FONTES.map(f => (
                <button
                  key={f.slug}
                  type="button"
                  onClick={() => toggleFonte(f.slug)}
                  className={`px-3 py-1 rounded-full text-xs font-semibold border transition-colors ${
                    fontesSel.includes(f.slug)
                      ? 'bg-primary text-primary-foreground border-primary'
                      : 'bg-background text-muted-foreground border-border hover:border-primary'
                  }`}
                >
                  {f.label}
                </button>
              ))}
            </div>
          </div>

          {/* Input de busca */}
          <form onSubmit={handlePesquisar} className="flex gap-2">
            <Input
              type="text"
              placeholder="Ex: diabetes, hipertensão gestante, DPOC..."
              value={termo}
              onChange={e => setTermo(e.target.value)}
              className="flex-1"
            />
            <Button type="submit" disabled={loading}>
              {loading
                ? <Loader2 className="w-4 h-4 animate-spin" />
                : <Search className="w-4 h-4" />
              }
              Pesquisar
            </Button>
          </form>

          {erro && (
            <div className="bg-destructive/10 text-destructive p-3 rounded-md text-sm">
              {erro}
            </div>
          )}

          {fontesCons.length > 0 && (
            <p className="text-xs text-muted-foreground">
              {resultados.length} resultado(s) · fontes: {fontesCons.join(', ')}
            </p>
          )}
        </CardContent>
      </Card>

      {/* Resultados */}
      {resultados.length > 0 && (
        <div className="space-y-4">
          {resultados.map((item, i) => (
            <Card key={item.url ?? item.doi ?? i}>
              <CardHeader className="pb-2">
                <CardTitle className="text-base leading-snug">
                  {item.url ? (
                    <a
                      href={item.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="hover:underline flex items-start gap-1"
                    >
                      {item.titulo}
                      <ExternalLink className="w-3 h-3 mt-1 shrink-0 opacity-60" />
                    </a>
                  ) : item.titulo}
                </CardTitle>
                <CardDescription className="flex flex-wrap items-center gap-2 mt-1">
                  <Badge variant="secondary">{item.fonte}</Badge>
                  {item.ano  && <span>{item.ano}</span>}
                  {item.tipo && <span className="text-xs uppercase">{item.tipo}</span>}
                  {item.doi  && <span className="text-xs opacity-60">DOI: {item.doi}</span>}
                  {item.pmid && <span className="text-xs opacity-60">PMID: {item.pmid}</span>}
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-2">
                {item.autores && item.autores.length > 0 && (
                  <p className="text-xs text-muted-foreground">
                    {item.autores.slice(0, 4).join('; ')}{item.autores.length > 4 ? ' et al.' : ''}
                  </p>
                )}
                {item.resumo && (
                  <p className="text-sm text-muted-foreground line-clamp-3">{item.resumo}</p>
                )}
                {item.referencia_abnt && (
                  <div className="flex items-start gap-2 bg-muted/50 rounded p-2">
                    <code className="text-xs flex-1 break-words">{item.referencia_abnt}</code>
                    <button
                      type="button"
                      onClick={() => copiar(item.referencia_abnt!, `ref-${i}`)}
                      className="shrink-0 text-muted-foreground hover:text-primary"
                      title="Copiar referência ABNT"
                    >
                      {copiado === `ref-${i}`
                        ? <CheckCheck className="w-4 h-4 text-green-500" />
                        : <Copy className="w-4 h-4" />
                      }
                    </button>
                  </div>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {!loading && resultados.length === 0 && termo && !erro && (
        <p className="text-center text-muted-foreground py-8">
          Nenhum resultado encontrado para "{termo}". Tente outro termo ou selecione mais fontes.
        </p>
      )}

      {/* Lista de referências completas */}
      {referencias.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">Referências Bibliográficas (ABNT)</CardTitle>
          </CardHeader>
          <CardContent>
            <ol className="space-y-2">
              {referencias.map((ref, i) => (
                <li key={i} className="text-xs text-muted-foreground flex gap-2">
                  <span className="shrink-0 font-semibold">{i + 1}.</span>
                  <span>{ref}</span>
                </li>
              ))}
            </ol>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

## 4. Uso na página — src/pages/Index.tsx

import { PesquisaSaude } from '@/components/PesquisaSaude';

export default function Index() {
  return (
    <div className="container py-8">
      <h1 className="text-2xl font-bold mb-6">Pesquisa em Saúde</h1>
      <PesquisaSaude />
    </div>
  );
}

## 5. Endpoints da API

Base URL: https://req.joaosmfilho.org
Autenticação: header X-API-Key obrigatório (exceto / e /api-key)

| Endpoint                  | Método | Descrição                                      |
|---------------------------|--------|------------------------------------------------|
| /pesquisar                | GET    | Busca geral — query string: q, fontes, limit   |
| /pesquisar                | POST   | Busca avançada com body JSON                   |
| /pesquisar/{fonte}        | GET    | Busca em fonte específica (mais rápido)         |
| /resposta                 | POST   | Texto formatado com citações ABNT embutidas    |
| /fontes                   | GET    | Lista as 8 fontes disponíveis                  |
| /status                   | GET    | Status operacional da API e de cada fonte      |
| /playground               | GET    | Interface visual para testar a API no browser  |
| /docs                     | GET    | Swagger UI com documentação interativa         |

Fontes disponíveis: pubmed · scielo · lilacs · ministerio · sbmfc · sbp · sbpt · sbc
```

---

## 🚀 Fontes Disponíveis

| Slug | Nome Completo | Tipo | Dados Retornados |
|------|---------------|------|-----------------|
| `pubmed` | PubMed (NCBI E-utilities) | Base científica | Título, abstract completo, DOI, PMID, journal, volume, issue, autores reais |
| `scielo` | SciELO | Base científica | Título, DOI, journal, autores, URL |
| `lilacs` | LILACS/BVS (BIREME) | Base científica | Título, autores, URL, ano |
| `ministerio` | Ministério da Saúde — PCDT | Oficial/GOV | Título do protocolo, URL gov.br, ano |
| `sbmfc` | SBMFC (Medicina de Família) | Sociedade médica | Título, resumo, URL, ano |
| `sbp` | SBP (Pediatria) | Sociedade médica | Título, resumo, URL, ano |
| `sbpt` | SBPT (Pneumologia) | Sociedade médica | Título, resumo, URL, ano |
| `sbc` | SBC (Cardiologia) | Sociedade médica | Título, resumo, URL, ano |

---

## 📝 Exemplos de Uso

### Pesquisa em todas as fontes
```typescript
import { pesquisar } from '@/lib/pesquisaSaude';

const { resultados, referencias_completas } = await pesquisar('diabetes tipo 2');
resultados.forEach(r => {
  console.log(r.titulo);
  console.log(r.referencia_abnt); // Ex: SILVA, JM. Effectiveness of… 2023. DOI: 10.1016/…
});
```

### Pesquisa em fontes específicas
```typescript
const pubmed = await pesquisar('hipertensão gestante', {
  fontes: ['pubmed', 'scielo', 'ministerio'],
  anoMin: 2020,
  limit: 15,
});
```

### Pesquisa em uma única fonte (endpoint dedicado)
```typescript
import { pesquisarPorFonte } from '@/lib/pesquisaSaude';

const { resultados } = await pesquisarPorFonte('pubmed', 'DPOC exacerbação', { limit: 10 });
```

### Resposta formatada com citações ABNT
```typescript
import { obterRespostaFormatada } from '@/lib/pesquisaSaude';

const { texto, referencias } = await obterRespostaFormatada('tratamento hipertensão gestacional');
// texto: "Background: Metformin remains… (SILVA, 2023).\n\n…(BRASIL, 2022)."
// referencias: ["SILVA, JM. Effectiveness of…", "BRASIL. Protocolo Clínico…"]
```

### Verificar status da API
```typescript
import { verificarStatus } from '@/lib/pesquisaSaude';

const status = await verificarStatus();
// { api_version: "3.0.0", status: "operacional", fontes: [...], cache_entries: 42 }
```

---

## 🔗 Links Úteis

| Recurso | URL |
|---------|-----|
| **Playground interativo** | https://req.joaosmfilho.org/playground |
| **Swagger UI** | https://req.joaosmfilho.org/docs |
| **ReDoc** | https://req.joaosmfilho.org/redoc |
| **Status da API** | https://req.joaosmfilho.org/status *(requer X-API-Key)* |
| **GitHub** | https://github.com/joaofilhosm/pesquisa-saude |
