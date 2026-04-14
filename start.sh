#!/bin/bash
# Script de inicialização para repo-panel
# Nota: Ignora argumentos passados pelo repo-panel (-l 3099)

# Obter diretório absoluto do script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Ativar venv
. .venv/bin/activate

# Adicionar backend-python ao PYTHONPATH
export PYTHONPATH="${SCRIPT_DIR}/backend-python:${PYTHONPATH}"

# Iniciar uvicorn
# Argumentos $@ são ignorados propositalmente
python -m uvicorn api.main:app \
    --host 0.0.0.0 \
    --port "${PORT:-8001}" \
    --log-level info
