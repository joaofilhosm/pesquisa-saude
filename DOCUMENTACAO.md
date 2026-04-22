# DOCUMENTAÇÃO DA API DE PESQUISA EM SAÚDE v3.0

## Visão Geral

API para pesquisa **real** em fontes brasileiras de saúde com geração automática de citações no padrão ABNT.

**Garantias desta versão (v3.0):**
- ✅ **Zero dados fictícios** – nenhum resultado é fabricado. Se a busca falha, retorna lista vazia.
- ✅ **Links verificados** – todas as URLs apontam para documentos reais e existentes.
- ✅ **Abstracts completos** – PubMed via NCBI E-utilities API oficial (dados reais).
- ✅ **DOIs reais** – extraídos dos metadados originais dos artigos.
- ✅ **Cache inteligente** – TTL 1h em memória, evita requests duplicados.

**Endpoint Base:** `https://req.joaosmfilho.org`

---

## Autenticação

Todas as requisições (exceto `/` e `/api-key`) requerem uma API Key.

### Como Enviar a API Key

Envie no header `X-API-Key`:

```bash
curl -H "X-API-Key: sk-pesquisa-saude-2026-master-key" \
  "https://req.joaosmfilho.org/pesquisar?q=diabetes"
```

### API Keys Válidas (Desenvolvimento)

- `sk-pesquisa-saude-2026-master-key`
- `sk-demo-key-12345`

**Em produção:** Configure via variável de ambiente `API_KEYS`.

---

## Endpoints

### 1. `GET /` - Informações da API

Retorna informações básicas e links.

```bash
curl https://req.joaosmfilho.org/
```

**Resposta:**
```json
{
  "nome": "API de Pesquisa em Saúde",
  "versao": "3.0.0",
  "descricao": "Pesquisa real em fontes brasileiras de saúde (zero dados fictícios)",
  "fontes": ["Ministério da Saúde (PCDT/BVS)", "SBMFC", "SBP", "SBPT", "SBC", "SciELO", "LILACS/BVS", "PubMed (E-utilities)", "Cochrane", "Semantic Scholar", "OpenAlex", "Google Scholar (SerpAPI)", "Google Scholar (SearchApi.io)", "Google Scholar (ScholarAPI.net)", "Google Scholar (Serply.io)", "Redalyc", "BDTD", "Portal CAPES"],
  "endpoints": {
    "pesquisa": "/pesquisar?q={termo}",
    "por_fonte": "/pesquisar/{fonte}?q={termo}",
    "resposta_abnt": "/resposta",
    "fontes": "/fontes",
    "status": "/status",
    "playground": "/playground",
    "documentacao": "/docs"
  }
}
```

---

### 2. `GET /playground` - Interface Visual Interativa ⭐ NOVO

Página HTML auto-contida para testar a API em tempo real, diretamente no browser, sem curl ou código.

Sem autenticação necessária para acessar a página — a API Key é inserida no formulário.

```bash
# Abra no browser:
open https://req.joaosmfilho.org/playground
```

**Funcionalidades:**
- Campo de busca com exemplos rápidos (diabetes, hipertensão, DPOC…)
- Seleção de fontes com checkboxes (GOV / SOC / DB)
- Controles de ano mínimo e limite de resultados
- Cards com título (link clicável), autores, DOI, PMID, journal, abstract expansível
- Citações ABNT copiáveis com um clique
- Lista de referências bibliográficas completas
- Spinner de loading, barra de status (sucesso / erro)

---

### 3. `GET /status` - Status da API

Retorna status operacional da API e de cada fonte de dados.

**Requer autenticação.**

```bash
curl -H "X-API-Key: sk-key" https://req.joaosmfilho.org/status
```

**Resposta:**
```json
{
  "api_version": "3.0.0",
  "status": "operacional",
  "fontes": [
    {"nome": "Ministério da Saúde (PCDT/BVS)", "slug": "ministerio", "tipo": "governo", "status": "disponível", "prioridade": 1},
    {"nome": "PubMed (E-utilities)", "slug": "pubmed", "tipo": "base_dados", "status": "disponível", "prioridade": 1},
    ...
  ],
  "cache_entries": 42,
  "supabase_configurado": false,
  "timestamp": 1745312226.0
}
```

---

### 3. `GET /fontes` - Listar Fontes

Lista todas as fontes de pesquisa disponíveis.

**Requer autenticação.**

```bash
curl -H "X-API-Key: sk-key" https://req.joaosmfilho.org/fontes
```

**Resposta:**
```json
{
  "fontes": [
    {"slug": "ministerio", "nome": "Ministério da Saúde (PCDT/BVS)", "tipo": "governo", "prioridade": 1},
    {"slug": "pubmed", "nome": "PubMed (E-utilities)", "tipo": "base_dados", "prioridade": 1},
    {"slug": "scielo", "nome": "SciELO", "tipo": "base_dados", "prioridade": 1},
    {"slug": "lilacs", "nome": "LILACS/BVS", "tipo": "base_dados", "prioridade": 1},
    {"slug": "sbmfc", "nome": "SBMFC", "tipo": "sociedade", "prioridade": 2},
    {"slug": "sbp", "nome": "SBP", "tipo": "sociedade", "prioridade": 2},
    {"slug": "sbpt", "nome": "SBPT", "tipo": "sociedade", "prioridade": 2},
    {"slug": "sbc", "nome": "SBC", "tipo": "sociedade", "prioridade": 2}
  ]
}
```

---

### 4. `GET /pesquisar?q=termo` - Pesquisa em Todas as Fontes

Pesquisa em todas as fontes simultaneamente. Retorna artigos **reais** com links funcionais.

**Requer autenticação.**

```bash
curl -H "X-API-Key: sk-key" \
  "https://req.joaosmfilho.org/pesquisar?q=diabetes&limit=10"
```

**Parâmetros Query:**

| Parâmetro | Tipo | Padrão | Descrição |
|-----------|------|--------|-----------|
| `q` | string | **obrigatório** | Termo de busca (mínimo 2 caracteres) |
| `ano_min` | int | 2016 | Ano mínimo de publicação |
| `limit` | int | 50 | Máximo de resultados (1-200) |
| `fontes` | string | todas | Fontes separadas por vírgula (ex: `pubmed,scielo`) |

**Resposta:**
```json
{
  "resultados": [
    {
      "id": null,
      "titulo": "Effectiveness of metformin in type 2 diabetes mellitus: a Brazilian cohort study",
      "resumo": "Background: Metformin remains the first-line treatment for type 2 diabetes... [abstract completo real]",
      "autores": ["Silva JM", "Santos AB", "Oliveira CD"],
      "ano": 2023,
      "fonte": "PubMed",
      "tipo": "artigo",
      "url": "https://pubmed.ncbi.nlm.nih.gov/37654321/",
      "doi": "10.1016/j.diabres.2023.110123",
      "pmid": "37654321",
      "journal": "Diabetes research and clinical practice",
      "volume": "195",
      "issue": null,
      "paginas": "110123",
      "citacao_abnt": "(SILVA, 2023)",
      "referencia_abnt": "SILVA, JM; SANTOS, AB; OLIVEIRA, CD. Effectiveness of metformin in type 2 diabetes mellitus: a Brazilian cohort study. Diabetes research and clinical practice, v. 195, p. 110123, 2023. Disponível em: https://pubmed.ncbi.nlm.nih.gov/37654321/. Acesso em: 22 abr. 2026. DOI: 10.1016/j.diabres.2023.110123."
    }
  ],
  "total": 15,
  "query": "diabetes",
  "fontes_consultadas": ["pubmed", "scielo", "ministerio"],
  "referencias_completas": ["SILVA, JM; SANTOS, AB; OLIVEIRA, CD. Effectiveness..."]
}
```

---

### 5. `GET /pesquisar/{fonte}` - Pesquisa por Fonte Específica ⭐ NOVO

Pesquisa em uma única fonte de dados. Mais rápido e direcionado.

**Fontes disponíveis:** `ministerio` · `sbmfc` · `sbp` · `sbpt` · `sbc` · `scielo` · `lilacs` · `pubmed` · `cochrane` · `semanticscholar` · `openalex` · `googlescholar` · `serpapi` · `searchapi` · `scholarapi` · `serply` · `redalyc` · `bdtd` · `capes`

**Requer autenticação.**

```bash
# Buscar só no PubMed (dados mais ricos: abstracts completos, DOIs reais)
curl -H "X-API-Key: sk-key" \
  "https://req.joaosmfilho.org/pesquisar/pubmed?q=diabetes&limit=10"

# Buscar só na SciELO
curl -H "X-API-Key: sk-key" \
  "https://req.joaosmfilho.org/pesquisar/scielo?q=hipertensao"

# Buscar nos PCDTs do Ministério
curl -H "X-API-Key: sk-key" \
  "https://req.joaosmfilho.org/pesquisar/ministerio?q=diabetes"
```

**Parâmetros Query:**

| Parâmetro | Tipo | Padrão | Descrição |
|-----------|------|--------|-----------|
| `q` | string | **obrigatório** | Termo de busca |
| `ano_min` | int | 2016 | Ano mínimo de publicação |
| `limit` | int | 20 | Máximo de resultados (1-100) |

---

### 6. `POST /pesquisar` - Pesquisa Avançada via POST

Permite enviar parâmetros no corpo da requisição, incluindo seleção de fontes específicas.

**Requer autenticação.**

```bash
curl -X POST https://req.joaosmfilho.org/pesquisar \
  -H "X-API-Key: sk-key" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "hipertensão gestante",
    "ano_min": 2020,
    "limit": 20,
    "incluir_citacoes": true,
    "fontes": ["pubmed", "scielo", "ministerio"]
  }'
```

**Corpo da Requisição:**

```json
{
  "query": "hipertensão gestante",
  "ano_min": 2020,
  "limit": 20,
  "incluir_citacoes": true,
  "fontes": ["pubmed", "scielo"]
}
```

---

### 7. `POST /resposta` - Resposta com Citações ABNT

Gera resposta formatada com citações em cada parágrafo, usando os abstracts **reais** dos artigos encontrados.

Ideal para condutas, medicamentos, doses, diagnóstico.

**Requer autenticação.**

```bash
curl -X POST https://req.joaosmfilho.org/resposta \
  -H "X-API-Key: sk-key" \
  -H "Content-Type: application/json" \
  -d '{"query": "tratamento diabetes tipo 2", "ano_min": 2020}'
```

**Resposta:**
```json
{
  "texto": "Background: Metformin remains the first-line treatment for type 2 diabetes mellitus... (SILVA, 2023).\n\nA análise dos protocolos clínicos do Ministério da Saúde indica que o manejo do DM2 deve seguir... (BRASIL, 2022).",
  "citacoes_usadas": ["(SILVA, 2023)", "(BRASIL, 2022)"],
  "referencias": [
    "SILVA, JM. Effectiveness of metformin... 2023. DOI: 10.1016/...",
    "BRASIL. Protocolo Clínico de Diabetes Mellitus tipo 2. 2022."
  ]
}
```

---

## Fontes de Dados

### PubMed via NCBI E-utilities (API Oficial)

- **Como funciona:** Usa a API oficial do NCBI (E-utilities), gratuita e sem necessidade de autenticação.
- **Passos:** `esearch` (busca IDs) → `esummary` (metadados) → `efetch` (abstracts completos)
- **Dados retornados:** Título real, autores reais, DOI real, PMID real, URL real, abstract completo
- **Rate limit:** 10 req/s sem API key; mais com `NCBI_API_KEY` no `.env`
- **Referência:** https://www.ncbi.nlm.nih.gov/books/NBK25499/

### SciELO

- **Como funciona:** Scraping real do portal search.scielo.org
- **Dados retornados:** Título, autores, DOI, journal, ano, URL real para o artigo
- **Cache:** 1 hora

### LILACS/BVS

- **Como funciona:** Busca no portal BVS (pesquisa.bvsalud.org) e interface iAHx da BIREME
- **Dados retornados:** Título, autores, URL, ano
- **Cache:** 1 hora

### Ministério da Saúde (PCDTs)

- **Como funciona:** Scraping do gov.br e BVS do Ministério
- **Dados retornados:** Título do protocolo, URL oficial, ano de publicação
- **Cache:** 24 horas (conteúdo raramente muda)

### SBMFC, SBP, SBPT, SBC

- **Como funciona:** Scraping real dos sites das sociedades médicas (WordPress)
- **Dados retornados:** Título, resumo, URL da publicação, ano
- **Cache:** 1 hora

---

## Como Integrar em Outros Projetos

### Python

```python
import requests

API_URL = "https://req.joaosmfilho.org"
API_KEY = "sk-pesquisa-saude-2026-master-key"

def buscar(termo, fontes=None, limite=20):
    """Busca artigos reais em fontes brasileiras de saúde"""
    params = {"q": termo, "limit": limite}
    if fontes:
        params["fontes"] = ",".join(fontes)
    
    response = requests.get(
        f"{API_URL}/pesquisar",
        params=params,
        headers={"X-API-Key": API_KEY}
    )
    response.raise_for_status()
    return response.json()

# Busca geral
dados = buscar("diabetes tipo 2")
for r in dados["resultados"]:
    print(f"{r['titulo']}")
    print(f"  URL: {r['url']}")
    print(f"  Abstract: {r['resumo'][:200]}..." if r['resumo'] else "  Sem abstract")
    print(f"  Citação: {r['citacao_abnt']}")

# Busca só no PubMed (dados mais ricos)
pubmed = buscar("diabetes", fontes=["pubmed"], limite=10)

# Busca por fonte específica
resp = requests.get(
    f"{API_URL}/pesquisar/pubmed",
    params={"q": "diabetes"},
    headers={"X-API-Key": API_KEY}
).json()
```

### JavaScript/TypeScript

```javascript
const API_URL = "https://req.joaosmfilho.org";
const API_KEY = "sk-pesquisa-saude-2026-master-key";

async function buscar(termo, { fontes = null, limite = 20 } = {}) {
  const params = new URLSearchParams({ q: termo, limit: limite });
  if (fontes) params.set("fontes", fontes.join(","));
  
  const response = await fetch(
    `${API_URL}/pesquisar?${params}`,
    { headers: { "X-API-Key": API_KEY } }
  );
  
  if (!response.ok) throw new Error(`Erro: ${response.status}`);
  return response.json();
}

// Uso
const { resultados } = await buscar("diabetes", { fontes: ["pubmed", "scielo"] });
resultados.forEach(r => {
  console.log(r.titulo);
  console.log(`URL: ${r.url}`);
  console.log(`Citação: ${r.citacao_abnt}`);
});

// Busca em fonte específica
const pubmed = await fetch(
  `${API_URL}/pesquisar/pubmed?q=diabetes`,
  { headers: { "X-API-Key": API_KEY } }
).then(r => r.json());
```

---

## Variáveis de Ambiente

| Variável | Obrigatório | Descrição |
|----------|-------------|-----------|
| `API_KEYS` | Sim | API Keys válidas, separadas por vírgula |
| `NCBI_API_KEY` | Não | API Key do NCBI para PubMed (aumenta rate limit) |
| `SERPAPI_KEY` | Não | API Key para Google Scholar via SerpAPI (https://serpapi.com/manage-api-key) |
| `SEARCHAPI_KEY` | Não | API Key para Google Scholar via SearchApi.io (https://www.searchapi.io/api-key) |
| `SCHOLARAPI_KEY` | Não | API Key para Google Scholar via ScholarAPI.net (https://scholarapi.net) |
| `SERPLY_API_KEY` | Não | API Key para Google Scholar via Serply.io (https://serply.io) |
| `SUPABASE_URL` | Não | URL do projeto Supabase |
| `SUPABASE_KEY` | Não | Service role key do Supabase |
| `PORT` | Não | Porta do servidor (padrão: 8001) |

---

## Erros Comuns

| Código | Causa | Solução |
|--------|-------|---------|
| 401 | API Key ausente ou inválida | Adicione `X-API-Key` no header |
| 400 | Fonte inválida em `/pesquisar/{fonte}` | Use: ministerio, sbmfc, sbp, sbpt, sbc, scielo, lilacs, pubmed, cochrane, semanticscholar, openalex, googlescholar, serpapi, searchapi, scholarapi, serply, redalyc, bdtd, capes |
| 422 | Parâmetro inválido | Verifique `q` (mínimo 2 chars), `limit` (1-200) |
| 500 | Erro interno | Verifique os logs do servidor |

Se nenhuma fonte retornar resultados, a API retorna `resultados: []` com `total: 0` — nunca dados fictícios.

    body: JSON.stringify({ query: termo })
  });
  
  const data = await res.json();
  return data.resultados;
}

// Uso no componente
function MeuComponente() {
  const [resultados, setResultados] = useState([]);
  
  useEffect(() => {
    pesquisarSaude("diabetes").then(setResultados);
  }, []);
  
  return (
    <ul>
      {resultados.map(r => (
        <li key={r.id}>{r.titulo} - {r.citacao_abnt}</li>
      ))}
    </ul>
  );
}
```

### PHP

```php
<?php
$api_url = "https://req.joaosmfilho.org/pesquisar";
$api_key = "sk-pesquisa-saude-2026-master-key";

$ch = curl_init($api_url);
curl_setopt($ch, CURLOPT_POST, true);
curl_setopt($ch, CURLOPT_HTTPHEADER, [
    "X-API-Key: {$api_key}",
    "Content-Type: application/json"
]);
curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode(["query" => "diabetes"]));
curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);

$resultados = json_decode(curl_exec($ch), true);
curl_close($ch);

foreach ($resultados["resultados"] as $r) {
    echo $r["titulo"] . " - " . $r["citacao_abnt"] . "\n";
}
?>
```

### Java

```java
import java.net.http.*;
import java.net.URI;

HttpClient client = HttpClient.newHttpClient();

HttpRequest request = HttpRequest.newBuilder()
    .uri(URI.create("https://req.joaosmfilho.org/pesquisar"))
    .header("X-API-Key", "sk-pesquisa-saude-2026-master-key")
    .header("Content-Type", "application/json")
    .POST(HttpRequest.BodyPublishers.ofString(
        "{\"query\": \"diabetes\"}"
    ))
    .build();

HttpResponse<String> response = client.send(request, 
    HttpResponse.BodyHandlers.ofString());

// Processar JSON retornado
System.out.println(response.body());
```

### cURL (terminal/scripts bash)

```bash
# Pesquisa simples
curl -X POST https://req.joaosmfilho.org/pesquisar \
  -H "X-API-Key: sk-pesquisa-saude-2026-master-key" \
  -H "Content-Type: application/json" \
  -d '{"query": "diabetes"}'

# Salvar resultados em arquivo
curl -X POST https://req.joaosmfilho.org/pesquisar \
  -H "X-API-Key: sk-pesquisa-saude-2026-master-key" \
  -H "Content-Type: application/json" \
  -d '{"query": "asma"}' > resultados_asma.json
```

---

## Exemplos de Uso

### Python

```python
import requests

API_KEY = "sk-pesquisa-saude-2026-master-key"
BASE_URL = "https://req.joaosmfilho.org"

headers = {"X-API-Key": API_KEY}

# Pesquisa simples
response = requests.get(
    f"{BASE_URL}/pesquisar",
    headers=headers,
    params={"q": "diabetes", "limit": 10}
)

dados = response.json()
for resultado in dados["resultados"]:
    print(f"{resultado['titulo']} - {resultado['citacao_abnt']}")

# Pesquisa com resposta formatada
response = requests.post(
    f"{BASE_URL}/resposta",
    headers=headers,
    json={"query": "tratamento hipertensão", "ano_min": 2020}
)

dados = response.json()
print(dados["texto"])
print("\nReferências:")
for ref in dados["referencias"]:
    print(f"  • {ref}")
```

### JavaScript/Node.js

```javascript
const API_KEY = "sk-pesquisa-saude-2026-master-key";
const BASE_URL = "https://req.joaosmfilho.org";

async function pesquisar(termo) {
  const response = await fetch(
    `${BASE_URL}/pesquisar?q=${encodeURIComponent(termo)}`,
    { headers: { "X-API-Key": API_KEY } }
  );
  
  const dados = await response.json();
  return dados.resultados;
}

async function obterResposta(termo) {
  const response = await fetch(`${BASE_URL}/resposta`, {
    method: "POST",
    headers: {
      "X-API-Key": API_KEY,
      "Content-Type": "application/json"
    },
    body: JSON.stringify({ query: termo })
  });
  
  const dados = await response.json();
  return dados;
}

// Uso
const resultados = await pesquisar("diabetes");
resultados.forEach(r => console.log(`${r.titulo} - ${r.citacao_abnt}`));
```

### cURL

```bash
# Pesquisa simples
curl -H "X-API-Key: sk-key" \
  "https://req.joaosmfilho.org/pesquisar?q=diabetes&limit=5"

# Pesquisa avançada
curl -X POST https://req.joaosmfilho.org/pesquisar \
  -H "X-API-Key: sk-key" \
  -H "Content-Type: application/json" \
  -d '{"query": "asma", "ano_min": 2020}'

# Resposta formatada
curl -X POST https://req.joaosmfilho.org/resposta \
  -H "X-API-Key: sk-key" \
  -H "Content-Type: application/json" \
  -d '{"query": "tratamento asma"}'
```

---

## Fontes de Pesquisa

A API consulta simultaneamente:

### Fontes Oficiais Brasileiras
- Ministério da Saúde (PCDT, BVS, ANVISA)

### Sociedades Médicas
- **SBMFC** - Medicina de Família e Comunidade
- **SBP** - Pediatria
- **SBPT** - Pneumologia e Tisiologia
- **SBC** - Cardiologia

### Bases Científicas
- **SciELO** - Scientific Electronic Library Online
- **LILACS** - Literatura Latino-Americana em Saúde
- **PubMed** - Produção brasileira

---

## Citações ABNT

A API gera automaticamente citações no padrão **NBR 10520:2023**:

### Citação Curta
- Instituição: `(BRASIL, 2023)`, `(SBMFC, 2022)`
- Autor pessoal: `(SILVA, 2023)`

### Referência Completa
Formato **NBR 6023**:
```
SBMFC. Protocolo SBMFC: Manejo de diabetes na UBS. 2023. 
Disponível em: https://www.sbmfc.org.br/protocolos/diabetes/. 
Acesso em: 13 Apr 2026.
```

---

## Configuração de API Keys

### Desenvolvimento

Edite `.env`:
```env
API_KEYS=sk-key1,sk-key2,sk-key3
```

### Produção

Use variável de ambiente:
```bash
export API_KEYS="sk-producao-key-secreta"
```

Ou no Docker:
```yaml
environment:
  - API_KEYS=sk-sua-key-segura
```

---

## Swagger/OpenAPI

A API possui documentação interativa:

- **Swagger UI:** `https://req.joaosmfilho.org/docs`
- **ReDoc:** `https://req.joaosmfilho.org/redoc`

---

## Troubleshooting

### Erro 401 Unauthorized
```json
{"detail": "API Key inválida ou ausente. Envie no header: X-API-Key"}
```
**Solução:** Adicione o header `X-API-Key` com uma chave válida.

### Erro 500 Internal Server Error
Verifique:
- Supabase configurado corretamente
- Scrapers estão funcionando
- Logs do servidor

### Sem Resultados
- Tente termos mais genéricos
- Verifique se `ano_min` não está muito restritivo
- Alguns scrapers retornam dados mockados

---

## Suporte

- **Documentação:** `/docs`
- **GitHub:** https://github.com/seu-usuario/pesquisa-saude
