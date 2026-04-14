# Como Iniciar a API de Pesquisa em Saúde

## Passo 1: Criar Tabelas no Supabase (OBRIGATÓRIO)

1. Acesse: https://supabase.com/dashboard/project/xqujpkdlxvldlsqpqnkj/sql/new
2. Clique em "New query"
3. Copie TODO o conteúdo de `supabase/schema_completo.sql`
4. Cole no editor SQL
5. Clique em "Run" (Ctrl+Enter)
6. Confirme que apareceu "Success"

## Passo 2: Iniciar os Servidores

### Opção A: Script automático (Windows)

```bash
./iniciar.bat
```

### Opção B: Manual (2 terminais)

**Terminal 1 - Backend Python:**
```bash
cd backend-python
python -m uvicorn api.main:app --reload --port 8000
```

**Terminal 2 - Backend Node.js:**
```bash
cd backend-node
npm run dev
```

## Passo 3: Testar

**Terminal 3:**
```bash
python test_api.py
```

Ou acesse no navegador:
- http://localhost:3000 (API Node.js)
- http://localhost:8000 (API Python)
- http://localhost:3000/pesquisar?q=diabetes (Teste de pesquisa)

## Endpoints Disponíveis

| Endpoint | Descrição |
|----------|-----------|
| `GET /` | Informações da API |
| `GET /fontes` | Lista fontes disponíveis |
| `GET /pesquisar?q=termo` | Pesquisa simples |
| `POST /pesquisar` | Pesquisa avançada |
| `POST /resposta` | Gera resposta com citações ABNT |
| `GET /pcdt?termo=x` | Busca no PCDT |
| `GET /protocolos/ubs` | Protocolos para UBS |
| `GET /urgencia` | Protocolos de urgência |

## Exemplo de Uso com cURL

```bash
# Pesquisa simples
curl "http://localhost:3000/pesquisar?q=hipertensao&limit=5"

# Pesquisa com citações ABNT
curl -X POST http://localhost:3000/resposta ^
  -H "Content-Type: application/json" ^
  -d "{\"query\": \"tratamento diabetes tipo 2\", \"ano_min\": 2016}"
```
