# DOCUMENTAÇÃO DA API DE PESQUISA EM SAÚDE

## Visão Geral

API para pesquisa em fontes brasileiras de saúde com geração automática de citações no padrão ABNT.

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
- `sk-test-key-67890`

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
  "versao": "2.0.0",
  "fontes": ["Ministério da Saúde", "SBMFC", "SBP", "SciELO", ...],
  "documentacao": "/docs",
  "como_obter_key": "/api-key"
}
```

---

### 2. `GET /api-key` - Obter Informações de Autenticação

Retorna informações sobre como usar a API Key.

```bash
curl https://req.joaosmfilho.org/api-key
```

**Resposta:**
```json
{
  "message": "API Key necessária para acesso",
  "api_key": "sk-pesquisa-saude-2026-master-key",
  "como_usar": {
    "curl": "curl -H \"X-API-Key: sk-sua-key\" \"https://req.joaosmfilho.org/pesquisar?q=diabetes\"",
    "python": "requests.get(url, headers={\"X-API-Key\": \"sk-sua-key\"})",
    "javascript": "fetch(url, {headers: {\"X-API-Key\": \"sk-sua-key\"}})"
  }
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
    {"nome": "Ministério da Saúde - PCDT", "tipo": "ministerio", "prioridade": 1},
    {"nome": "SBMFC", "tipo": "sociedade", "prioridade": 2},
    {"nome": "SciELO", "tipo": "base_dados", "prioridade": 1},
    ...
  ]
}
```

---

### 4. `GET /pesquisar?q=termo` - Pesquisa Simples

Pesquisa em todas as fontes simultaneamente.

**Requer autenticação.**

```bash
curl -H "X-API-Key: sk-key" \
  "https://req.joaosmfilho.org/pesquisar?q=diabetes&limit=10"
```

**Parâmetros Query:**

| Parâmetro | Tipo | Padrão | Descrição |
|-----------|------|--------|-----------|
| `q` | string | **obrigatório** | Termo de busca |
| `ano_min` | int | 2016 | Ano mínimo (últimos 10 anos) |
| `limit` | int | 50 | Máximo de resultados |

**Resposta:**
```json
{
  "resultados": [
    {
      "id": "uuid-...",
      "titulo": "Protocolo SBMFC: Manejo de diabetes na UBS",
      "resumo": "A Sociedade Brasileira de Medicina de Família...",
      "autores": null,
      "ano": 2023,
      "fonte": "SBMFC",
      "tipo": "protocolo",
      "url": "https://www.sbmfc.org.br/...",
      "doi": null,
      "citacao_abnt": "(SBMFC, 2023)",
      "referencia_abnt": "SBMFC. Protocolo SBMFC..."
    }
  ],
  "total": 7,
  "query": "diabetes",
  "referencias_completas": ["SBMFC. Protocolo...", "..."]
}
```

---

### 5. `POST /pesquisar` - Pesquisa Avançada

Permite enviar parâmetros no corpo da requisição.

**Requer autenticação.**

```bash
curl -X POST https://req.joaosmfilho.org/pesquisar \
  -H "X-API-Key: sk-key" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "hipertensão gestante",
    "ano_min": 2020,
    "limit": 20,
    "incluir_citacoes": true
  }'
```

**Corpo da Requisição:**

```json
{
  "query": "hipertensão gestante",
  "ano_min": 2020,
  "limit": 20,
  "incluir_citacoes": true
}
```

---

### 6. `POST /resposta` - Resposta com Citações ABNT

Gera resposta formatada com citações em cada parágrafo.

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
  "texto": "A metformina é o fármaco de primeira escolha... (SBMFC, 2023).\n\nO acompanhamento deve incluir avaliação renal... (BRASIL, 2022).",
  "citacoes_usadas": ["(SBMFC, 2023)", "(BRASIL, 2022)"],
  "referencias": [
    "SBMFC. Protocolo SBMFC: Diabetes tipo 2. 2023.",
    "BRASIL. Protocolo Clínico de Diabetes. 2022."
  ]
}
```

---

## Como Integrar em Outros Projetos

A API roda como um serviço HTTP independente. Seus outros projetos acessam via URL.

### Fluxo de Integração

```
┌─────────────────┐      HTTP Request       ┌──────────────────────┐
│  SEU PROJETO    │ ──────────────────────> │  API Pesquisa Saúde  │
│  (qualquer um)  │                         │  (localhost:8001)    │
│                 │ <────────────────────── │                      │
└─────────────────┘      JSON Response      └──────────────────────┘
```

### Passo a Passo

1. **Inicie a API** (uma vez):
```bash
cd backend-python/api
python -m uvicorn main:app --host 0.0.0.0 --port 8001
```

2. **Acesse de qualquer projeto** usando a URL `http://localhost:8001`

3. **Envie a API Key** no header `X-API-Key`

4. **Receba os resultados** diretamente no seu projeto

---

## Exemplos de Integração

### Python (qualquer projeto Python)

```python
import requests

# Configuração
API_URL = "https://req.joaosmfilho.org"
API_KEY = "sk-pesquisa-saude-2026-master-key"

def buscar_no_seu_projeto(termo):
    response = requests.post(
        f"{API_URL}/pesquisar",
        headers={"X-API-Key": API_KEY},
        json={"query": termo}
    )
    return response.json()["resultados"]

# Uso no seu projeto
resultados = buscar_no_seu_projeto("diabetes")
for r in resultados:
    print(f"Título: {r['titulo']}")
    print(f"Citação ABNT: {r['citacao_abnt']}")
```

### Node.js / JavaScript

```javascript
const API_URL = "https://req.joaosmfilho.org";
const API_KEY = "sk-pesquisa-saude-2026-master-key";

async function buscarNoSeuProjeto(termo) {
  const response = await fetch(`${API_URL}/pesquisar`, {
    method: "POST",
    headers: {
      "X-API-Key": API_KEY,
      "Content-Type": "application/json"
    },
    body: JSON.stringify({ query: termo })
  });
  
  const data = await response.json();
  return data.resultados;
}

// Uso no seu projeto
const resultados = await buscarNoSeuProjeto("hipertensão");
console.log(resultados);
```

### React / Frontend

```javascript
// componente/PesquisaSaude.jsx
async function pesquisarSaude(termo) {
  const res = await fetch("https://req.joaosmfilho.org/pesquisar", {
    method: "POST",
    headers: {
      "X-API-Key": "sk-pesquisa-saude-2026-master-key",
      "Content-Type": "application/json"
    },
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
