# Integração com Projetos Lovable

Prompt copia e cola para integrar a API de Pesquisa em Saúde em projetos criados com [Lovable](https://lovable.dev).

---

## 📋 Prompt para Lovable

Copie e cole este prompt no Lovable para integrar a API de Pesquisa em Saúde:

```
Adicione integração com a API de Pesquisa em Saúde brasileira.

## Configuração

Crie um arquivo `.env.local` com:
```
VITE_API_URL=https://req.joaosmfilho.org
VITE_API_KEY=sk-pesquisa-saude-2026-master-key
```

## Hook/Utility

Crie `src/lib/pesquisaSaude.ts`:
```typescript
const API_URL = import.meta.env.VITE_API_URL || 'https://req.joaosmfilho.org';
const API_KEY = import.meta.env.VITE_API_KEY || 'sk-pesquisa-saude-2026-master-key';

export interface ResultadoPesquisa {
  id: string;
  titulo: string;
  resumo: string;
  autores: string | null;
  ano: number;
  fonte: string;
  tipo: string;
  url: string;
  doi: string | null;
  citacao_abnt: string;
  referencia_abnt: string;
}

export interface RespostaFormatada {
  texto: string;
  citacoes_usadas: string[];
  referencias: string[];
}

export async function pesquisar(termo: string, limit: number = 50): Promise<ResultadoPesquisa[]> {
  const response = await fetch(`${API_URL}/pesquisar`, {
    method: 'POST',
    headers: {
      'X-API-Key': API_KEY,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ query: termo, limit }),
  });
  
  if (!response.ok) throw new Error('Erro na pesquisa');
  const data = await response.json();
  return data.resultados;
}

export async function obterRespostaFormatada(query: string): Promise<RespostaFormatada> {
  const response = await fetch(`${API_URL}/resposta`, {
    method: 'POST',
    headers: {
      'X-API-Key': API_KEY,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ query }),
  });
  
  if (!response.ok) throw new Error('Erro ao obter resposta');
  return response.json();
}
```

## Componente de Pesquisa

Crie `src/components/PesquisaSaude.tsx`:
```tsx
import { useState } from 'react';
import { pesquisar, obterRespostaFormatada, type ResultadoPesquisa } from '@/lib/pesquisaSaude';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Loader2, Search, FileText } from 'lucide-react';

export function PesquisaSaude() {
  const [termo, setTermo] = useState('');
  const [resultados, setResultados] = useState<ResultadoPesquisa[]>([]);
  const [loading, setLoading] = useState(false);
  const [erro, setErro] = useState<string | null>(null);

  const handlePesquisar = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!termo.trim()) return;

    setLoading(true);
    setErro(null);
    try {
      const dados = await pesquisar(termo);
      setResultados(dados);
    } catch (err) {
      setErro('Erro ao pesquisar. Tente novamente.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card className="w-full max-w-4xl mx-auto">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Search className="w-5 h-5" />
          Pesquisa em Saúde
        </CardTitle>
        <CardDescription>
          Busque em fontes brasileiras: Ministério da Saúde, SBMFC, SBP, SciELO e outras
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handlePesquisar} className="flex gap-2 mb-6">
          <Input
            type="text"
            placeholder="Ex: diabetes, hipertensão, asma..."
            value={termo}
            onChange={(e) => setTermo(e.target.value)}
            className="flex-1"
          />
          <Button type="submit" disabled={loading}>
            {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Search className="w-4 h-4" />}
            Pesquisar
          </Button>
        </form>

        {erro && (
          <div className="bg-destructive/10 text-destructive p-3 rounded-md mb-4">
            {erro}
          </div>
        )}

        {resultados.length > 0 && (
          <div className="space-y-4">
            <h3 className="font-semibold text-lg">
              {resultados.length} resultado(s) encontrado(s)
            </h3>
            {resultados.map((item) => (
              <Card key={item.id}>
                <CardHeader>
                  <CardTitle className="text-base">{item.titulo}</CardTitle>
                  <CardDescription className="flex items-center gap-2">
                    <span className="font-medium">{item.fonte}</span>
                    <span>•</span>
                    <span>{item.ano}</span>
                    <span>•</span>
                    <span className="text-xs uppercase">{item.tipo}</span>
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  {item.resumo && (
                    <p className="text-sm text-muted-foreground mb-3">{item.resumo}</p>
                  )}
                  <div className="flex items-center justify-between">
                    <code className="text-xs bg-muted px-2 py-1 rounded">
                      {item.citacao_abnt}
                    </code>
                    {item.url && (
                      <Button variant="link" size="sm" asChild>
                        <a href={item.url} target="_blank" rel="noopener noreferrer">
                          Ver fonte <FileText className="w-3 h-3 ml-1" />
                        </a>
                      </Button>
                    )}
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}

        {!loading && resultados.length === 0 && termo && (
          <p className="text-center text-muted-foreground py-8">
            Nenhum resultado encontrado para "{termo}"
          </p>
        )}
      </CardContent>
    </Card>
  );
}
```

## Uso na Página

Em `src/pages/Index.tsx` ou outra página:
```tsx
import { PesquisaSaude } from '@/components/PesquisaSaude';

export default function Index() {
  return (
    <div className="container py-8">
      <PesquisaSaude />
    </div>
  );
}
```

## Documentação da API

- **Base URL:** https://req.joaosmfilho.org
- **Endpoints:**
  - `POST /pesquisar` - Pesquisa com parâmetros no body
  - `GET /pesquisar?q=termo` - Pesquisa simples via query string
  - `POST /resposta` - Resposta formatada com citações ABNT
  - `GET /fontes` - Lista todas as fontes
- **Autenticação:** Header `X-API-Key`
- **Swagger:** https://req.joaosmfilho.org/docs
```

---

## 🚀 Fontes Disponíveis

A API pesquisa em:

| Fonte | Tipo | Prioridade |
|-------|------|------------|
| Ministério da Saúde - PCDT | Oficial | 1 |
| SciELO | Base científica | 1 |
| SBMFC | Sociedade médica | 2 |
| SBP (Pediatria) | Sociedade médica | 2 |
| SBPT (Pneumologia) | Sociedade médica | 2 |
| SBC (Cardiologia) | Sociedade médica | 2 |
| LILACS | Base científica | 1 |
| PubMed | Base científica | 2 |

---

## 📝 Exemplos de Uso

### Pesquisa Simples
```typescript
import { pesquisar } from '@/lib/pesquisaSaude';

const resultados = await pesquisar('diabetes tipo 2');
console.log(resultados[0].titulo);
console.log(resultados[0].citacao_abnt);
```

### Resposta Formatada com Citações ABNT
```typescript
import { obterRespostaFormatada } from '@/lib/pesquisaSaude';

const resposta = await obterRespostaFormatada('tratamento hipertensão gestacional');
console.log(resposta.texto); // Texto com citações (SBMFC, 2023)
console.log(resposta.referencias); // Lista completa de referências
```

---

## 🔗 Links Úteis

- **Documentação completa:** `/docs` neste repositório
- **Swagger UI:** https://req.joaosmfilho.org/docs
- **ReDoc:** https://req.joaosmfilho.org/redoc
- **GitHub:** https://github.com/joaofilhosm/pesquisa-saude
