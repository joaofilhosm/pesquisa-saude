#!/bin/bash
# Script de inicialização para repo-panel
# Nota: Ignora argumentos passados pelo repo-panel (-l 3099)

# Obter diretório absoluto do script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Adicionar backend-python ao PYTHONPATH (antes de ativar venv)
export PYTHONPATH="${SCRIPT_DIR}/backend-python"

# Ativar venv
cd "${SCRIPT_DIR}"
. .venv/bin/activate

# Re-exportar PYTHONPATH após ativar venv
export PYTHONPATH="${SCRIPT_DIR}/backend-python"

# Porta: recebe do repo-panel via argumento -l ou variavel PORT, usa 8001 se nao definida
# Nunca usar 3000 ou 8089
USE_PORT=""

# Tentar argumento -l primeiro
while getopts "l:" opt; do
    case $opt in
        l) USE_PORT="$OPTARG" ;;
    esac
done

# Se nao passou -l, tentar variavel PORT
if [ -z "$USE_PORT" ] && [ -n "$PORT" ] && [ "$PORT" != "3000" ] && [ "$PORT" != "8089" ]; then
    USE_PORT=$PORT
fi

# Default para 8001
if [ -z "$USE_PORT" ]; then
    USE_PORT=8001
fi

echo "=== API de Pesquisa em Saúde ==="
echo "Port: $USE_PORT"
echo "PYTHONPATH: $PYTHONPATH"

# Matar processo existente na porta (se houver)
echo "Checking for existing process on port $USE_PORT..."
if command -v fuser >/dev/null 2>&1; then
    fuser -k "${USE_PORT}/tcp" 2>/dev/null && echo "Port $USE_PORT freed." || true
else
    EXISTING_PID=$(ss -tlnp 2>/dev/null | grep ":${USE_PORT} " | grep -oP 'pid=\K[0-9]+' | head -1)
    if [ -n "$EXISTING_PID" ]; then
        echo "Killing existing process (PID: $EXISTING_PID) on port $USE_PORT..."
        kill -15 "$EXISTING_PID" 2>/dev/null || true
        sleep 1
        kill -9 "$EXISTING_PID" 2>/dev/null || true
        echo "Port $USE_PORT freed."
    fi
fi
sleep 1

# Iniciar uvicorn
.venv/bin/python -m uvicorn api.main:app \
    --host 0.0.0.0 \
    --port "$USE_PORT" \
    --log-level info
