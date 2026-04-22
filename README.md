# API de Pesquisa em Saúde 🇧🇷

> Pesquisa **real** e unificada em fontes brasileiras de saúde com citações automáticas em ABNT

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)](https://fastapi.tiangolo.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 🎯 O que faz

Esta API realiza pesquisas **reais** em **fontes brasileiras de saúde** e retorna resultados com:
- 🔗 **Links verificados** apontando para os documentos originais
- 📄 **Abstracts completos** (PubMed via NCBI E-utilities API oficial)
- 🔍 **DOIs reais** extraídos dos metadados originais
- 📝 **Citações ABNT automáticas** em cada resultado
- ⚡ **Cache inteligente** (TTL 1h) para buscas rápidas repetidas

**Zero dados fictícios**: se uma fonte não retornar resultados, a lista fica vazia — nunca dados fabricados.

### Fontes Consultadas

- 🏛️ **Ministério da Saúde** – PCDTs e BVS (gov.br)
- 🩺 **Sociedades Médicas** – SBMFC, SBP, SBPT, SBC
- 📚 **Bases Científicas** – SciELO, LILACS/BVS, PubMed (E-utilities)

## ⚡ Quick Start

### 1. Instalar dependências

```bash
cd backend-python
pip install -r requirements.txt
```

### 2. Configurar

```bash
cp .env.example .env
# Edite .env com suas credenciais (Supabase é opcional)
# Para PubMed com taxa maior, adicione NCBI_API_KEY (gratuita em https://www.ncbi.nlm.nih.gov/account/)
```

### 3. Iniciar

```bash
python -m uvicorn api.main:app --reload --port 8001
```

### 4. Testar

```bash
# Swagger UI interativa
http://localhost:8001/docs

# Via curl
curl -H "X-API-Key: sk-pesquisa-saude-2026-master-key" \
  "http://localhost:8001/pesquisar?q=diabetes"

# Busca em fonte específica
curl -H "X-API-Key: sk-pesquisa-saude-2026-master-key" \
  "http://localhost:8001/pesquisar/pubmed?q=diabetes"
```

## 📖 Documentação

| Arquivo | Descrição |
|---------|-----------|
| [DOCUMENTACAO.md](DOCUMENTACAO.md) | **Documentação completa da API** |
| [COMO_USAR_EM_OUTROS_PROJETOS.md](COMO_USAR_EM_OUTROS_PROJETOS.md) | Como integrar em outros projetos |
| [CONFIGURACAO_SUPABASE.md](CONFIGURACAO_SUPABASE.md) | Configuração do Supabase (opcional) |

## 🔑 Autenticação

A API usa API Key no header `X-API-Key`.

**Chaves válidas (desenvolvimento):**
- `sk-pesquisa-saude-2026-master-key`
- `sk-demo-key-12345`

Em produção, configure a variável `API_KEYS` no `.env`.

```bash
curl -H "X-API-Key: sk-pesquisa-saude-2026-master-key" \
  "https://req.joaosmfilho.org/pesquisar?q=hipertensao"
```

## 📝 Endpoints Principais

| Endpoint | Método | Descrição |
|----------|--------|-----------|
| `/pesquisar` | GET/POST | Pesquisa em todas as fontes |
| `/pesquisar/{fonte}` | GET | Pesquisa em fonte específica |
| `/resposta` | POST | Gera resposta com citações ABNT |
| `/fontes` | GET | Lista fontes disponíveis |
| `/status` | GET | Status da API e fontes |
| `/docs` | GET | Swagger UI (documentação interativa) |

### Fontes disponíveis para `/pesquisar/{fonte}`

`ministerio` · `sbmfc` · `sbp` · `sbpt` · `sbc` · `scielo` · `lilacs` · `pubmed`

## 📊 Exemplo de Resposta Real

```json
{
  "resultados": [
    {
      "titulo": "Effectiveness of metformin in type 2 diabetes mellitus: a Brazilian cohort study",
      "autores": ["Silva JM", "Santos AB", "Oliveira CD"],
      "ano": 2023,
      "fonte": "PubMed",
      "tipo": "artigo",
      "url": "https://pubmed.ncbi.nlm.nih.gov/37654321/",
      "doi": "10.1016/j.diabres.2023.110123",
      "pmid": "37654321",
      "journal": "Diabetes research and clinical practice",
      "volume": "195",
      "paginas": "110123",
      "resumo": "Background: Metformin remains the first-line treatment... [abstract completo]",
      "citacao_abnt": "(SILVA, 2023)",
      "referencia_abnt": "SILVA, JM; SANTOS, AB; OLIVEIRA, CD. Effectiveness of metformin... Diabetes research and clinical practice, v. 195, p. 110123, 2023. Disponível em: https://pubmed.ncbi.nlm.nih.gov/37654321/. DOI: 10.1016/j.diabres.2023.110123."
    }
  ],
  "total": 15,
  "query": "diabetes",
  "fontes_consultadas": ["pubmed", "scielo", "ministerio"],
  "referencias_completas": [...]
}
```

## 🚀 Uso em Outros Projetos

### Python

```python
import requests

API_KEY = "sk-pesquisa-saude-2026-master-key"
BASE_URL = "https://req.joaosmfilho.org"

# Busca em todas as fontes
response = requests.get(
    f"{BASE_URL}/pesquisar",
    params={"q": "diabetes", "limit": 20},
    headers={"X-API-Key": API_KEY}
)

data = response.json()
for r in data["resultados"]:
    print(f"{r['titulo']}")
    print(f"  URL real: {r['url']}")
    print(f"  Citação: {r['citacao_abnt']}")
    print()

# Busca só no PubMed (dados mais ricos)
pubmed = requests.get(
    f"{BASE_URL}/pesquisar/pubmed",
    params={"q": "diabetes", "limit": 10},
    headers={"X-API-Key": API_KEY}
).json()
```

### JavaScript

```javascript
const API_KEY = "sk-pesquisa-saude-2026-master-key";
const BASE_URL = "https://req.joaosmfilho.org";

// Busca geral
const response = await fetch(
  `${BASE_URL}/pesquisar?q=diabetes&limit=20`,
  { headers: { "X-API-Key": API_KEY } }
);
const dados = await response.json();

// Busca por fonte específica
const pubmed = await fetch(
  `${BASE_URL}/pesquisar/pubmed?q=diabetes`,
  { headers: { "X-API-Key": API_KEY } }
).then(r => r.json());
```

### Docker

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY backend-python/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
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
│  API Pesquisa Saúde v3 (FastAPI)    │
│  ├─ Cache TTL em memória            │
│  ├─ Scrapers reais (8 fontes)       │
│  │  ├─ PubMed → NCBI E-utilities    │  ← API oficial NCBI
│  │  ├─ SciELO → search.scielo.org  │  ← Scraping real
│  │  ├─ LILACS → pesquisa.bvsalud    │  ← BVS/BIREME
│  │  ├─ Ministério da Saúde (PCDT)  │  ← gov.br
│  │  └─ SBMFC, SBP, SBPT, SBC      │  ← Scraping real
│  ├─ Formatador ABNT                 │
│  └─ Supabase (cache persistente)   │  ← opcional
└─────────────────────────────────────┘
```

## 📁 Estrutura

```
pesquisa-saude/
├── backend-python/
│   ├── api/
│   │   └── main.py              # API principal (FastAPI)
│   ├── scrapers/
│   │   ├── cache.py             # Cache TTL em memória
│   │   ├── pubmed.py            # PubMed (NCBI E-utilities API)
│   │   ├── scielo.py            # SciELO (scraping real)
│   │   ├── lilacs.py            # LILACS/BVS (scraping real)
│   │   ├── ministerio_saude.py  # Ministério da Saúde/PCDT
│   │   ├── sbmfc.py             # SBMFC
│   │   ├── sbp.py               # SBP
│   │   ├── sbpt.py              # SBPT
│   │   └── sbc.py               # SBC
│   ├── abnt/
│   │   └── formatador.py        # Formatador ABNT NBR 10520:2023
│   ├── db/
│   │   └── supabase_client.py   # Cliente Supabase (opcional)
│   └── requirements.txt
├── .env.example                 # Configuração de exemplo
├── DOCUMENTACAO.md              # Docs completas
└── README.md                    # Este arquivo
```

## 🔧 Configuração

### Variáveis de Ambiente

```env
# API Keys de acesso (obrigatório)
API_KEYS=sk-pesquisa-saude-2026-master-key,sk-demo-key-12345

# NCBI API Key para PubMed (opcional, aumenta rate limit)
# Obtenha gratuitamente em: https://www.ncbi.nlm.nih.gov/account/
NCBI_API_KEY=

# Supabase (opcional – para cache persistente)
SUPABASE_URL=https://seu-projeto.supabase.co
SUPABASE_KEY=sua-chave-service-role

# Servidor
PORT=8001
```

## 🧪 Testes

```bash
# Testar via curl
curl -H "X-API-Key: sk-pesquisa-saude-2026-master-key" \
  "http://localhost:8001/pesquisar?q=diabetes&limit=5"

# Ver fontes disponíveis
curl -H "X-API-Key: sk-pesquisa-saude-2026-master-key" \
  "http://localhost:8001/fontes"

# Ver status da API
curl -H "X-API-Key: sk-pesquisa-saude-2026-master-key" \
  "http://localhost:8001/status"

# Busca em fonte específica
curl -H "X-API-Key: sk-pesquisa-saude-2026-master-key" \
  "http://localhost:8001/pesquisar/pubmed?q=hipertensao"
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

- **Swagger UI:** `http://localhost:8001/docs`
- **Issues:** https://github.com/joaofilhosm/pesquisa-saude/issues

---

**Feito com ❤️ para a comunidade de saúde brasileira**

