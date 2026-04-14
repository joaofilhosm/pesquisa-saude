#!/bin/bash
# Script de inicialização para repo-panel
# Nota: Ignora argumentos passados pelo repo-panel (-l 3099)

# Ativar venv
. .venv/bin/activate

# Iniciar uvicorn
# Argumentos $@ são ignorados propositalmente
python -m uvicorn backend-python.api.main:app \
    --host 0.0.0.0 \
    --port "${PORT:-8001}" \
    --log-level info
