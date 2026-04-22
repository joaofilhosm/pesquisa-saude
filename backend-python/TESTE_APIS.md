# Guia de Teste das APIs Google Scholar

## Configuração

Adicione as chaves no arquivo `.env` (uma por vez ou todas juntas):

```env
# Teste SerpAPI
SERPAPI_KEY=sua-chave-aqui

# Teste SearchApi.io
SEARCHAPI_KEY=sua-chave-aqui

# Teste ScholarAPI.net
SCHOLARAPI_KEY=sua-chave-aqui

# Teste Serply.io
SERPLY_API_KEY=sua-chave-aqui
```

## Obtenção das Chaves

| API | URL | Plano Gratuito |
|-----|-----|----------------|
| SerpAPI | https://serpapi.com/manage-api-key | 100 buscas/mês |
| SearchApi.io | https://www.searchapi.io/api-key | 100 buscas/mês |
| ScholarAPI.net | https://scholarapi.net | Ver pricing |
| Serply.io | https://serply.io | 100 buscas/mês |

## Teste Individual via Curl

### 1. Testar SerpAPI

```bash
# 1. Adicione ao .env:
echo "SERPAPI_KEY=sua-chave" >> .env

# 2. Inicie a API (se não estiver rodando):
uvicorn api.main:app --reload --port 8001

# 3. Teste:
curl -H "X-API-Key: sk-pesquisa-saude-2026-master-key" \
  -H "Content-Type: application/json" \
  -d '{"query": "diabetes tipo 2", "fontes": ["serpapi"], "limit": 5}' \
  http://localhost:8001/pesquisar
```

### 2. Testar SearchApi.io

```bash
echo "SEARCHAPI_KEY=sua-chave" >> .env

curl -H "X-API-Key: sk-pesquisa-saude-2026-master-key" \
  -H "Content-Type: application/json" \
  -d '{"query": "diabetes tipo 2", "fontes": ["searchapi"], "limit": 5}' \
  http://localhost:8001/pesquisar
```

### 3. Testar ScholarAPI.net

```bash
echo "SCHOLARAPI_KEY=sua-chave" >> .env

curl -H "X-API-Key: sk-pesquisa-saude-2026-master-key" \
  -H "Content-Type: application/json" \
  -d '{"query": "diabetes tipo 2", "fontes": ["scholarapi"], "limit": 5}' \
  http://localhost:8001/pesquisar
```

### 4. Testar Serply.io

```bash
echo "SERPLY_API_KEY=sua-chave" >> .env

curl -H "X-API-Key: sk-pesquisa-saude-2026-master-key" \
  -H "Content-Type: application/json" \
  -d '{"query": "diabetes tipo 2", "fontes": ["serply"], "limit": 5}' \
  http://localhost:8001/pesquisar
```

## Teste via Playground

1. Acesse: http://localhost:8001/playground
2. Cole sua API Key no campo "🔑 API Key"
3. Desmarque todas as fontes
4. Marque **apenas** a fonte que deseja testar:
   - [ ] Google Scholar (SerpAPI)
   - [ ] Google Scholar (SearchApi)
   - [ ] Google Scholar (ScholarAPI)
   - [ ] Google Scholar (Serply)
5. Digite um termo: `diabetes tipo 2`
6. Clique em "Pesquisar"

## Script de Teste Automático

Existe um script pronto em `test_google_scholar_apis.py`:

```bash
# Configure as chaves no .env primeiro
export SERPAPI_KEY="sua-chave"
export SEARCHAPI_KEY="sua-chave"
export SCHOLARAPI_KEY="sua-chave"
export SERPLY_API_KEY="sua-chave"

# Execute o teste
python test_google_scholar_apis.py
```

## Critérios de Sucesso

Cada API deve retornar:
- ✅ Status HTTP 200
- ✅ Pelo menos 1 resultado (depende do termo)
- ✅ Campos preenchidos: `titulo`, `url`, `fonte`
- ✅ Campo `ano` presente (quando disponível)
- ✅ Campo `doi` presente (quando disponível)

## Troubleshooting

### Erro 401 (Unauthorized)
- API Key inválida ou expirada
- Verifique em https://serpapi.com/manage-api-key (ou equivalente)

### Erro 429 (Rate Limit)
- Limite de requisições atingido
- Aguarde ou upgrade do plano

### Resultados vazios []
- Termo de busca muito específico
- API Key configurada mas sem créditos
- Verifique logs da API

### Timeout
- Aumentar `HTTP_TIMEOUT=60` no .env
