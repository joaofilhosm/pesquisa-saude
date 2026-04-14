#!/bin/bash
# Script de inicialização para repo-panel

# Ativar venv
. .venv/bin/activate

# Iniciar uvicorn com logging configurado
# Ignora argumentos extras como -l 3099
python -m uvicorn backend-python.api.main:app \
    --host 0.0.0.0 \
    --port "${PORT:-8001}" \
    --log-level info
