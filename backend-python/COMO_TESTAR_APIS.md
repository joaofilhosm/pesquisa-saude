# Como Testar Cada API Google Scholar Individualmente

## Contexto

As 4 APIs do Google Scholar foram adicionadas:
- **SerpAPI** (`SERPAPI_KEY`)
- **SearchApi.io** (`SEARCHAPI_KEY`)
- **ScholarAPI.net** (`SCHOLARAPI_KEY`)
- **Serply.io** (`SERPLY_API_KEY`)

As chaves estão configuradas no **repo-panel** como variáveis de ambiente.

---

## Método 1: Teste via Playground (Recomendado)

### Passo a passo:

1. **Acesse o Playground**
   ```
   https://req.joaosmfilho.org/playground
   ```

2. **Cole sua API Key** no campo "🔑 API Key"
   ```
   sk-pesquisa-saude-2026-master-key
   ```

3. **Desmarque todas as fontes** (clique em "Desmarcar todas")

4. **Marque APENAS a fonte que quer testar:**
   - [ ] Google Scholar (SerpAPI) ← teste uma por vez
   - [ ] Google Scholar (SearchApi)
   - [ ] Google Scholar (ScholarAPI)
   - [ ] Google Scholar (Serply)

5. **Digite o termo de busca:**
   ```
   diabetes tipo 2
   ```

6. **Clique em "Pesquisar"**

7. **Verifique o resultado:**
   - ✅ Sucesso: cards com artigos reais
   - ❌ Erro: mensagem na barra de status

8. **Repita** para cada uma das 4 APIs

---

## Método 2: Teste via Curl (Terminal)

### Testar SerpAPI:
```bash
curl -X POST "https://req.joaosmfilho.org/pesquisar" \
  -H "X-API-Key: sk-pesquisa-saude-2026-master-key" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "diabetes tipo 2",
    "fontes": ["serpapi"],
    "limit": 3
  }' | python3 -m json.tool
```

### Testar SearchApi.io:
```bash
curl -X POST "https://req.joaosmfilho.org/pesquisar" \
  -H "X-API-Key: sk-pesquisa-saude-2026-master-key" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "diabetes tipo 2",
    "fontes": ["searchapi"],
    "limit": 3
  }' | python3 -m json.tool
```

### Testar ScholarAPI.net:
```bash
curl -X POST "https://req.joaosmfilho.org/pesquisar" \
  -H "X-API-Key: sk-pesquisa-saude-2026-master-key" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "diabetes tipo 2",
    "fontes": ["scholarapi"],
    "limit": 3
  }' | python3 -m json.tool
```

### Testar Serply.io:
```bash
curl -X POST "https://req.joaosmfilho.org/pesquisar" \
  -H "X-API-Key: sk-pesquisa-saude-2026-master-key" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "diabetes tipo 2",
    "fontes": ["serply"],
    "limit": 3
  }' | python3 -m json.tool
```

---

## Método 3: Script Automático

Quando a API estiver rodando (via repo-panel ou local):

```bash
cd /data/repos/joaofilhosm__pesquisa-saude/backend-python

# Testa todas as APIs configuradas
python3 test_apis_runtime.py
```

---

## Critérios de Sucesso

Cada API deve retornar:

| Critério | Esperado |
|----------|----------|
| HTTP Status | `200 OK` |
| Total de resultados | `> 0` (pelo menos 1) |
| Título | Preenchido |
| URL | Válida e funcional |
| Fonte | Nome correto da API |
| Ano | Presente (quando disponível) |

### Exemplo de resposta válida:
```json
{
  "total": 3,
  "resultados": [
    {
      "titulo": "Metformin in type 2 diabetes...",
      "ano": 2023,
      "fonte": "Google Scholar (SerpAPI)",
      "url": "https://pubmed.ncbi.nlm.nih.gov/12345678/",
      "doi": "10.1016/j.diabres.2023.110123"
    }
  ]
}
```

---

## Troubleshooting

### Erro: "Nenhum resultado encontrado"
- Termo de busca pode ser muito específico
- Tente termos mais genéricos: "diabetes", "hipertensão"

### Erro: "401 Unauthorized"
- API Key inválida
- Verifique se está usando `sk-pesquisa-saude-2026-master-key`

### Erro: "500 Internal Server Error"
- API pode estar com problema de configuração
- Verifique os logs no repo-panel

### Erro: "429 Too Many Requests"
- Limite de requisições da API atingido
- Aguarde alguns minutos ou teste outra API

---

## Variáveis de Ambiente no Repo-Panel

Verifique se estas variáveis estão configuradas:

```
SERPAPI_KEY=pk_...
SEARCHAPI_KEY=...
SCHOLARAPI_KEY=...
SERPLY_API_KEY=...
```

**Importante:** O repo-panel injeta essas variáveis no runtime da API.
O script `test_apis_runtime.py` lê essas variáveis do ambiente.

---

## Links Úteis

| API | Dashboard | Docs |
|-----|-----------|------|
| SerpAPI | https://serpapi.com/manage-api-key | https://serpapi.com/google-scholar-api |
| SearchApi.io | https://www.searchapi.io/dashboard | https://www.searchapi.io/docs/google-scholar |
| ScholarAPI.net | https://scholarapi.net/dashboard | https://scholarapi.net/docs |
| Serply.io | https://serply.io/dashboard | https://serply.io/docs |
