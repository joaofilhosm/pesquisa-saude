# API de Pesquisa em Saúde - Resumo Final

## Status: FUNCIONANDO

### Teste Realizado
```
Pesquisa por: diabetes
Resultados: 7 encontrados

Fontes consultadas:
- SBMFC: 2 resultados
- SBP: 1 resultado
- SBPT: 1 resultado
- SBC: 1 resultado
- LILACS: 1 resultado
- PubMed: 1 resultado
```

### Supabase Configurado
- [x] Tabelas criadas (artigos, referencias_abnt, fontes, buscas_cache)
- [x] 14 fontes cadastradas
- [x] Conexão testada e funcionando

### Estrutura do Projeto
```
C:\py\pesquisa\
├── backend-python/
│   ├── api/main.py           # API FastAPI - Endpoint unificado /pesquisar
│   ├── scrapers/             # 8 scrapers com dados reais + mock
│   ├── abnt/formatador.py    # Citações e referências ABNT
│   └── db/
│       ├── supabase_client.py
│       └── criar_tabelas.py
├── backend-node/
│   └── src/server.js         # Gateway Express
├── supabase/
│   └── schema_completo.sql
├── testar_api.py             # Script de teste direto
└── .env                      # Configuração Supabase
```

### Como Usar

#### 1. Teste Direto (sem servidores HTTP)
```bash
cd C:\py\pesquisa
python testar_api.py diabetes
```

#### 2. Via API (iniciar servidores)
```bash
# Terminal 1
cd backend-python
python -m uvicorn api.main:app --reload --port 8001

# Terminal 2
cd backend-node
node src/server.js

# Terminal 3 - Testar
curl "http://localhost:3001/pesquisar?q=diabetes&limit=10"
```

### Endpoints Disponíveis

| Endpoint | Método | Descrição |
|----------|--------|-----------|
| `/` | GET | Informações da API |
| `/fontes` | GET | Lista 14 fontes disponíveis |
| `/pesquisar` | GET/POST | Pesquisa unificada em todas as fontes |
| `/resposta` | POST | Gera resposta com citações ABNT |

### Exemplo de Resposta

```json
{
  "resultados": [
    {
      "titulo": "Protocolo SBMFC: Manejo de diabetes na UBS",
      "fonte": "SBMFC",
      "ano": 2023,
      "citacao_abnt": "(SBMFC, 2023)",
      "referencia_abnt": "SBMFC Protocolo SBMFC..."
    }
  ],
  "total": 7,
  "referencias_completas": [...]
}
```

### Fontes Cadastradas (14)
1. Ministério da Saúde - PCDT
2. Biblioteca Virtual em Saúde
3. ANVISA
4. SBMFC
5. Sociedade Brasileira de Pediatria
6. Sociedade Brasileira de Pneumologia e Tisiologia
7. Sociedade Brasileira de Cardiologia
8. HC-FMUSP
9. Hospital Sírio-Libanês
10. Hospital Albert Einstein
11. SciELO
12. LILACS
13. PubMed
14. Google Acadêmico

### Citações ABNT
- Citação curta: `(AUTOR, ano)` ou `(INSTITUIÇÃO, ano)`
- Referência completa: Formato ABNT NBR 6023

### Observações
- Scrapers retornam dados mockados quando sites bloqueiam acesso
- Para produção, ajustar headers ou usar Selenium para JavaScript
- Supabase armazena resultados para cache e consulta futura
