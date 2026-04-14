# API de Pesquisa em Saúde 🇧🇷

> Pesquisa unificada em fontes brasileiras de saúde com citações automáticas em ABNT

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)](https://fastapi.tiangolo.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 🎯 O que faz

Esta API realiza pesquisas em **fontes brasileiras de saúde** e retorna resultados com **citações ABNT automáticas**.

### Fontes Consultadas

- 🏛️ **Ministério da Saúde** (PCDT, BVS, ANVISA)
- 🩺 **Sociedades Médicas** (SBMFC, SBP, SBPT, SBC)
- 📚 **Bases Científicas** (SciELO, LILACS, PubMed)

## ⚡ Quick Start

### 1. Instalar dependências

```bash
cd backend-python
pip install -r requirements.txt
```

### 2. Configurar

```bash
# Copie e edite o .env
cp .env.example .env
```

Edite `.env` com suas credenciais do Supabase.

### 3. Iniciar

```bash
python -m uvicorn api.main:app --reload --port 8001
```

### 4. Testar

```bash
# Abra no navegador
http://localhost:8001/docs

# Ou via curl
curl -H "X-API-Key: sk-pesquisa-saude-2026-master-key" \
  "http://localhost:8001/pesquisar?q=diabetes"
```

## 📖 Documentação

| Arquivo | Descrição |
|---------|-----------|
| [DOCUMENTACAO.md](DOCUMENTACAO.md) | **Documentação completa da API** |
| [COMO_USAR_EM_OUTROS_PROJETOS.md](COMO_USAR_EM_OUTROS_PROJETOS.md) | Como integrar em outros projetos |
| [CONFIGURACAO_SUPABASE.md](CONFIGURACAO_SUPABASE.md) | Configuração do Supabase |

## 🔑 Autenticação

A API usa API Key no header `X-API-Key`.

**Chaves válidas (desenvolvimento):**
- `sk-pesquisa-saude-2026-master-key`
- `sk-demo-key-12345`

**Exemplo:**
```bash
curl -H "X-API-Key: sk-pesquisa-saude-2026-master-key" \
  "http://localhost:8001/pesquisar?q=hipertensao"
```

## 📝 Endpoints Principais

| Endpoint | Método | Descrição |
|----------|--------|-----------|
| `/pesquisar` | GET/POST | Pesquisa em todas as fontes |
| `/resposta` | POST | Gera resposta com citações ABNT |
| `/fontes` | GET | Lista fontes disponíveis |
| `/docs` | GET | Swagger UI (documentação interativa) |

## 📊 Exemplo de Resposta

```json
{
  "resultados": [
    {
      "titulo": "Protocolo SBMFC: Manejo de diabetes na UBS",
      "fonte": "SBMFC",
      "ano": 2023,
      "citacao_abnt": "(SBMFC, 2023)",
      "referencia_abnt": "SBMFC. Protocolo SBMFC..."
    }
  ],
  "total": 7,
  "referencias_completas": [...]
}
```

## 🚀 Uso em Outros Projetos

### Python

```python
import requests

API_KEY = "sk-pesquisa-saude-2026-master-key"

response = requests.get(
    "http://localhost:8001/pesquisar?q=diabetes",
    headers={"X-API-Key": API_KEY}
)

for r in response.json()["resultados"]:
    print(f"{r['titulo']} - {r['citacao_abnt']}")
```

### JavaScript

```javascript
const response = await fetch(
  "http://localhost:8001/pesquisar?q=diabetes",
  { headers: { "X-API-Key": "sk-pesquisa-saude-2026-master-key" } }
);

const dados = await response.json();
dados.resultados.forEach(r => console.log(r.titulo));
```

### Docker

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY backend-python/requirements.txt .
RUN pip install -r requirements.txt
COPY backend-python/ .
EXPOSE 8001
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8001"]
```

## 🏗️ Arquitetura

```
┌─────────────────────────────────────┐
│  SEU PROJETO (qualquer linguagem)   │
│  - React, Vue, Django, Flask, etc.  │
└──────────────┬──────────────────────┘
               │ HTTP/JSON (API Key)
               ▼
┌─────────────────────────────────────┐
│  API Pesquisa Saúde (FastAPI)       │
│  ├─ Scrapers (8 fontes)             │
│  ├─ Formatador ABNT                 │
│  └─ Supabase (cache/banco)          │
└─────────────────────────────────────┘
```

## 📁 Estrutura

```
pesquisa-saude/
├── backend-python/
│   ├── api/main.py          # API principal
│   ├── scrapers/            # Scrapers das fontes
│   ├── abnt/                # Formatador ABNT
│   ├── db/                  # Cliente Supabase
│   └── requirements.txt     # Dependências
├── supabase/
│   └── schema.sql           # Schema do banco
├── .env                     # Configurações
├── .env.example             # Exemplo de configuração
├── DOCUMENTACAO.md          # Docs completas
└── README.md                # Este arquivo
```

## 🔧 Configuração

### Variáveis de Ambiente

```env
# Supabase
SUPABASE_URL=https://seu-projeto.supabase.co
SUPABASE_KEY=sua-chave-service-role

# API Keys (separe por vírgula)
API_KEYS=sk-sua-key-1,sk-sua-key-2

# Servidor
PORT=8001
```

## 🧪 Testes

```bash
# Testar API diretamente
python testar_api.py diabetes

# Testar endpoints
curl -H "X-API-Key: sk-key" "http://localhost:8001/fontes"
```

## 📄 Licença

MIT License - veja [LICENSE](LICENSE) para detalhes.

## 🤝 Contribuindo

1. Fork o projeto
2. Crie uma branch (`git checkout -b feature/nova-feature`)
3. Commit (`git commit -m 'Adiciona nova feature'`)
4. Push (`git push origin feature/nova-feature`)
5. Abra um Pull Request

## 📞 Suporte

- **Documentação:** `/docs`
- **Issues:** https://github.com/seu-usuario/pesquisa-saude/issues

---

**Feito com ❤️ para a comunidade de saúde brasileira**
