#!/bin/bash
# Script de inicialização para repo-panel
# Nota: Ignora argumentos passados pelo repo-panel (-l 3099)

# Obter diretório absoluto do script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Ativar venv
. .venv/bin/activate

# Adicionar backend-python ao PYTHONPATH
export PYTHONPATH="${SCRIPT_DIR}/backend-python:${PYTHONPATH}"

# Porta: recebe exclusivamente do repo-panel
USE_PORT=$PORT

echo "=== API de Pesquisa em Saúde ==="
echo "Port: $USE_PORT"
echo "PYTHONPATH: $PYTHONPATH"

# Iniciar uvicorn
python -m uvicorn api.main:app \
    --host 0.0.0.0 \
    --port "$USE_PORT" \
    --log-level info
