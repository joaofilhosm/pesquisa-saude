@echo off
echo ================================================
echo   API de Pesquisa em Saude - Inicializacao
echo ================================================
echo.

REM Verificar se .env existe
if not exist .env (
    echo [AVISO] Copiando .env.example para .env...
    copy .env.example .env
    echo [AVISO] Edite .env com suas credenciais do Supabase!
    echo.
)

REM Iniciar backend Python
echo [1/2] Iniciando backend Python (FastAPI)...
start "Backend Python" cmd /k "cd backend-python && python -m uvicorn api.main:app --reload --port 8000"
timeout /t 3 /nobreak >nul

REM Iniciar backend Node.js
echo [2/2] Iniciando backend Node.js...
start "Backend Node.js" cmd /k "cd backend-node && npm run dev"

echo.
echo ================================================
echo   Servidores iniciados!
echo   - Python: http://localhost:8000
echo   - Node.js: http://localhost:3000
echo ================================================
echo.
echo Pressione qualquer tecla para abrir o navegador...
pause >nul
start http://localhost:3000
