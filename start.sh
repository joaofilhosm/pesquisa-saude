#!/bin/bash
# Script de inicialização para repo-panel
# Nota: Ignora argumentos passados pelo repo-panel (-l 3099)

# Obter diretório absoluto do script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Ativar venv
. .venv/bin/activate

# Adicionar backend-python ao PYTHONPATH
export PYTHONPATH="${SCRIPT_DIR}/backend-python:${PYTHONPATH}"

# Porta: usa variaveis do repo-panel
# Tenta PORT, SERVER_PORT, APP_PORT ou usa 8001
if [ -n "$PORT" ]; then
    USE_PORT=$PORT
elif [ -n "$SERVER_PORT" ]; then
    USE_PORT=$SERVER_PORT
elif [ -n "$APP_PORT" ]; then
    USE_PORT=$APP_PORT
else
    USE_PORT=8001
fi

echo "=== API de Pesquisa em Saúde ==="
echo "Iniciando na porta: $USE_PORT"
echo "PYTHONPATH: $PYTHONPATH"

# Iniciar uvicorn
python -m uvicorn api.main:app \
    --host 0.0.0.0 \
    --port "$USE_PORT" \
    --log-level info
