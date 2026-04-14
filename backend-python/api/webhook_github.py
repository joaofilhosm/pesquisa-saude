"""
Webhook para espelhamento GitHub -> repo-panel em tempo real

Quando o GitHub notificar um push, este endpoint:
1. Valida a assinatura do webhook
2. Faz git pull automático
3. Reinicia a aplicação

Configure no GitHub:
- URL: https://req.joaosmfilho.org/webhook
- Secret: WEBHOOK_SECRET (variável de ambiente)
- Events: Push only
"""

import os
import subprocess
import hmac
import hashlib
from fastapi import APIRouter, Request, HTTPException, Header
from fastapi.responses import JSONResponse

router = APIRouter()

WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "seu-segredo-aqui")
REPO_PATH = os.getenv("REPO_PATH", "/data/repos/joaofilhosm__pesquisa-saude")


def verify_signature(payload: bytes, signature: str) -> bool:
    """Verifica a assinatura do webhook do GitHub."""
    if not signature:
        return False

    expected = "sha256=" + hmac.new(
        WEBHOOK_SECRET.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(signature, expected)


@router.post("/webhook")
async def github_webhook(
    request: Request,
    x_hub_signature_256: str = Header(None)
):
    """
    Endpoint para receber webhooks do GitHub.

    Acionado automaticamente quando há novo push no repositório.
    """
    body = await request.body()

    # Validar assinatura
    if not verify_signature(body, x_hub_signature_256):
        raise HTTPException(status_code=401, detail="Assinatura inválida")

    # Parse do payload
    import json
    payload = json.loads(body)

    # Verificar se é evento de push
    if payload.get("ref") != "refs/heads/main":
        return JSONResponse({"status": "ignored", "reason": "not main branch"})

    # Fazer git pull
    try:
        result = subprocess.run(
            ["git", "-C", REPO_PATH, "pull", "origin", "main"],
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode != 0:
            raise HTTPException(status_code=500, detail=f"Git pull failed: {result.stderr}")

        # Reiniciar aplicação (depende do repo-panel)
        # Opção 1: Tocar arquivo de reload
        reload_file = "/data/.reload"
        with open(reload_file, "w") as f:
            f.write("reload")

        return JSONResponse({
            "status": "success",
            "message": "Repositório espelhado com sucesso",
            "git_output": result.stdout,
            "reload_triggered": True
        })

    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=500, detail="Git pull timeout")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/webhook/status")
async def webhook_status():
    """Verifica o status do espelhamento."""
    import json

    try:
        result = subprocess.run(
            ["git", "-C", REPO_PATH, "log", "-1", "--oneline"],
            capture_output=True,
            text=True,
            timeout=10
        )

        last_commit = result.stdout.strip()

        result_remote = subprocess.run(
            ["git", "-C", REPO_PATH, "ls-remote", "origin", "main"],
            capture_output=True,
            text=True,
            timeout=10
        )

        remote_hash = result_remote.stdout.split()[0] if result_remote.stdout else None

        return {
            "local_commit": last_commit,
            "remote_hash": remote_hash,
            "synced": remote_hash and last_commit.startswith(remote_hash[:8])
        }
    except Exception as e:
        return {"error": str(e)}
