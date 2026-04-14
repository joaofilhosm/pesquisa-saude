# Como Usar a API de Pesquisa em Saúde em Outros Projetos

## Opção 1: API HTTP (Recomendado para produção)

### Instalando apenas o backend Python

```bash
# No seu projeto
pip install fastapi uvicorn httpx beautifulsoup4 supabase python-dotenv
```

### Estrutura mínima

```
seu-projeto/
└── pesquisa-saude/
    ├── api.py              # Copiar de backend-python/api/main.py
    ├── scrapers/           # Copiar pasta scrapers
    ├── abnt/               # Copiar pasta abnt
    └── .env                # Configurar Supabase
```

### Iniciar API

```bash
python -m uvicorn api:app --host 0.0.0.0 --port 8001
```

### Consumir de qualquer linguagem

**JavaScript/Node.js:**
```javascript
const response = await fetch('http://localhost:8001/pesquisar?q=diabetes');
const dados = await response.json();
console.log(dados.resultados);
```

**Python:**
```python
import requests

response = requests.get('http://localhost:8001/pesquisar', params={'q': 'diabetes'})
dados = response.json()
for r in dados['resultados']:
    print(f"{r['titulo']} - {r['citacao_abnt']}")
```

**cURL:**
```bash
curl "http://localhost:8001/pesquisar?q=diabetes&limit=10"
```

---

## Opção 2: Biblioteca Python (Uso direto sem HTTP)

### Instalar como pacote local

No projeto `backend-python`, criar `setup.py`:

```python
from setuptools import setup, find_packages

setup(
    name='pesquisa-saude',
    version='1.0.0',
    packages=find_packages(),
    install_requires=[
        'httpx',
        'beautifulsoup4',
        'lxml',
        'supabase',
        'python-dotenv',
    ],
)
```

### Usar em outro projeto Python

```bash
# No diretório backend-python
pip install -e .
```

```python
# No seu projeto
from pesquisa_saude.scrapers import SciELOScraper, MinisterioSaudeScraper
from pesquisa_saude.abnt import ABNTFormatador, Artigo
import asyncio

async def pesquisar(termo):
    scraper = SciELOScraper()
    resultados = await scraper.buscar(termo)
    
    formatador = ABNTFormatador()
    for r in resultados:
        artigo = Artigo.from_dict(r)
        print(formatador.formatar_citacao_curta(artigo))

asyncio.run(pesquisar('diabetes'))
```

---

## Opção 3: Docker (Produção)

### Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY backend-python/requirements.txt .
RUN pip install -r requirements.txt

COPY backend-python/ .

EXPOSE 8001

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8001"]
```

### docker-compose.yml

```yaml
version: '3.8'

services:
  pesquisa-api:
    build: .
    ports:
      - "8001:8001"
    environment:
      - SUPABASE_URL=${SUPABASE_URL}
      - SUPABASE_KEY=${SUPABASE_KEY}
    restart: unless-stopped
```

### Usar

```bash
docker-compose up -d
curl "http://localhost:8001/pesquisar?q=diabetes"
```

---

## Opção 4: Serverless (Vercel, AWS Lambda)

### Estrutura para Vercel

```
vercel.json:
{
  "builds": [{
    "src": "api/main.py",
    "use": "@vercel/python"
  }],
  "routes": [{
    "src": "/(.*)",
    "dest": "api/main.py"
  }]
}
```

### Deploy

```bash
vercel --prod
```

---

## Resumo das Opções

| Opção | Quando Usar | Complexidade |
|-------|-------------|--------------|
| API HTTP | Produção, múltiplas linguagens | Baixa |
| Biblioteca Python | Apenas Python, mais performance | Baixa |
| Docker | Produção com consistência | Média |
| Serverless | Baixo custo, escala automática | Média |

---

## Endpoints da API

```
GET  /                           # Info da API
GET  /fontes                     # Lista fontes
GET  /pesquisar?q=termo          # Pesquisa simples
POST /pesquisar                  # Pesquisa avançada
POST /pesquisar                  # Gera resposta com citações
```

## Parâmetros de Pesquisa

```json
{
  "query": "diabetes",
  "ano_min": 2016,
  "limit": 20,
  "incluir_citacoes": true
}
```

## Resposta

```json
{
  "resultados": [
    {
      "titulo": "...",
      "fonte": "SBMFC",
      "ano": 2023,
      "citacao_abnt": "(SBMFC, 2023)",
      "referencia_abnt": "..."
    }
  ],
  "total": 10,
  "referencias_completas": [...]
}
```
