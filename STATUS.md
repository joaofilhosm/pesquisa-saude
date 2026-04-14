# Status do Projeto - API de Pesquisa em Saúde

## Conclusões

### ✅ Concluído

1. **Estrutura do Projeto**
   - Backend Python (FastAPI) com scrapers
   - Backend Node.js (Express) como gateway
   - Módulo ABNT para citações

2. **Dependências Instaladas**
   - Python: fastapi, uvicorn, httpx, beautifulsoup4, lxml, supabase
   - Node: express, cors, axios, @supabase/supabase-js

3. **Configuração Supabase**
   - Credenciais configuradas nos arquivos .env
   - Projeto criado: https://supabase.com/dashboard/project/xqujpkdlxvldlsqpqnkj

4. **API Funcional**
   - Python rodando em http://localhost:8001
   - Node.js rodando em http://localhost:3001
   - Endpoints respondendo corretamente

### ⚠️ Pendente

1. **Criar Tabelas no Supabase**
   - É necessário executar o SQL manualmente via dashboard
   - URL: https://supabase.com/dashboard/project/xqujpkdlxvldlsqpqnkj/sql/new
   - Copiar SQL de `supabase/schema_completo.sql`

2. **Scrapers**
   - Estrutura criada, mas sites podem bloquear scraping automático
   - Pode ser necessário ajustar headers ou usar Selenium para JavaScript

## Como Iniciar

### 1. Criar Tabelas (Obrigatório)
```
1. Acesse: https://supabase.com/dashboard/project/xqujpkdlxvldlsqpqnkj/sql/new
2. Clique em "New query"
3. Copie e cole o conteúdo de supabase/schema_completo.sql
4. Clique em "Run"
```

### 2. Iniciar Servidores
```bash
# Terminal 1 - Python
cd backend-python
python -m uvicorn api.main:app --reload --port 8001

# Terminal 2 - Node
cd backend-node
npm run dev
```

### 3. Testar
```bash
# Testar API
curl http://localhost:3001/
curl http://localhost:3001/fontes
curl "http://localhost:3001/pesquisar?q=diabetes"
```

## Endpoints Disponíveis

| Endpoint | Método | Descrição |
|----------|--------|-----------|
| `/` | GET | Informações da API |
| `/fontes` | GET | Lista fontes disponíveis |
| `/pesquisar` | GET/POST | Pesquisa em múltiplas fontes |
| `/resposta` | POST | Gera resposta com citações ABNT |
| `/pcdt` | GET | Busca no PCDT |
| `/protocolos/ubs` | GET | Protocolos UBS |
| `/urgencia` | GET | Protocolos urgência |

## Estrutura de Arquivos

```
C:\py\pesquisa\
├── backend-python/
│   ├── api/main.py           # API FastAPI
│   ├── scrapers/             # Scrapers (ministerio, sbmfc, scielo, etc.)
│   ├── abnt/formatador.py    # Citações ABNT
│   └── db/supabase_client.py # Cliente Supabase
├── backend-node/
│   ├── src/server.js         # Gateway Express
│   └── .env                  # Configuração
├── supabase/
│   └── schema_completo.sql   # SQL para criar tabelas
├── .env                      # Configuração principal
├── README.md                 # Documentação completa
└── COMO_INICIAR.md           # Guia de inicialização
```

## Fontes Cadastradas

- Ministério da Saúde (PCDT, BVS, ANVISA)
- SBMFC, SBP, SBPT, SBC
- HC-FMUSP, Sírio-Libanês, Einstein
- SciELO, LILACS, PubMed, Google Acadêmico

## Citações ABNT

O módulo `abnt/formatador.py` formata automaticamente:
- Citação curta: `(BRASIL, 2023)`, `(SBMFC, 2022)`
- Referência completa conforme NBR 6023
