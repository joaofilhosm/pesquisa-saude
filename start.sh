#!/bin/bash
# Script de inicialização para repo-panel
# Nota: Ignora argumentos passados pelo repo-panel (-l 3099)

# Obter diretório absoluto do script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Ativar venv
. .venv/bin/activate

# Adicionar backend-python ao PYTHONPATH
export PYTHONPATH="${SCRIPT_DIR}/backend-python:${PYTHONPATH}"

# Porta: recebe do repo-panel, usa 8001 se nao definida
# Nunca usar 3000 ou 8089
if [ -n "$PORT" ] && [ "$PORT" != "3000" ] && [ "$PORT" != "8089" ]; then
    USE_PORT=$PORT
else
    USE_PORT=8001
fi

echo "=== API de Pesquisa em Saúde ==="
echo "Port: $USE_PORT"
echo "PYTHONPATH: $PYTHONPATH"

# Matar processo existente na porta (se houver)
echo "Checking for existing process on port $USE_PORT..."
EXISTING_PID=$(lsof -t -i:$USE_PORT 2>/dev/null || netstat -tlnp 2>/dev/null | grep ":$USE_PORT " | awk '{print $7}' | cut -d'/' -f1 || ss -tlnp 2>/dev/null | grep ":$USE_PORT " | awk '{print $7}' | cut -d'/' -f1)
if [ -n "$EXISTING_PID" ]; then
    echo "Killing existing process (PID: $EXISTING_PID) on port $USE_PORT..."
    kill -9 $EXISTING_PID 2>/dev/null || true
    sleep 1
    echo "Port $USE_PORT freed."
fi

# Iniciar uvicorn
.venv/bin/python -m uvicorn api.main:app \
    --host 0.0.0.0 \
    --port "$USE_PORT" \
    --log-level info
