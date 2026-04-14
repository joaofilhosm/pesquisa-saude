#!/bin/bash
# Script de inicialização para repo-panel

# Ativar venv
. .venv/bin/activate

# Iniciar uvicorn com logging configurado
# O repo-panel passa LOG_PORT ou usa porta padrão
python -m uvicorn backend-python.api.main:app \
    --host 0.0.0.0 \
    --port "${PORT:-8001}" \
    --log-level info
