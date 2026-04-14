# Espelhamento GitHub → repo-panel (Tempo Real)

## Configuração no GitHub

1. Acesse: `https://github.com/joaofilhosm/pesquisa-saude/settings/hooks`

2. Clique em **"Add webhook"**

3. Preencha:

| Campo | Valor |
|-------|-------|
| **Payload URL** | `http://req.joaosmfilho.org/api/webhook` |
| **Content type** | `application/json` |
| **Secret** | `mesmo-segredo-do-repo-panel` |
| **SSL verification** | Disabled (se HTTP) |
| **Just the push event** | ✅ Selecionado |

4. Clique em **Add webhook**

---

## Configuração no repo-panel

Adicione a variável de ambiente:

```env
WEBHOOK_SECRET=seu-segredo-aqui
REPO_PATH=/data/repos/joaofilhosm__pesquisa-saude
```

---

## Como Funciona

```
┌─────────────┐      Push       ┌──────────────┐
│   GitHub    │ ──────────────> │  Webhook     │
│  (push)     │   JSON payload  │  /api/webhook│
└─────────────┘                 └──────────────┘
                                       │
                                       ▼
                                ┌──────────────┐
                                │ 1. Valida    │
                                │    assinatura│
                                └──────────────┘
                                       │
                                       ▼
                                ┌──────────────┐
                                │ 2. git pull  │
                                │    origin    │
                                └──────────────┘
                                       │
                                       ▼
                                ┌──────────────┐
                                │ 3. Trigger   │
                                │    reload    │
                                └──────────────┘
                                       │
                                       ▼
                                ┌──────────────┐
                                │  Aplicação   │
                                │  atualizada  │
                                └──────────────┘
```

---

## Teste o Webhook

### Pelo GitHub:
1. Vá em **Settings > Webhooks**
2. Clique no webhook criado
3. Clique em **"Redeliver"**

### Via curl:
```bash
curl -X POST http://req.joaosmfilho.org/api/webhook \
  -H "Content-Type: application/json" \
  -H "X-Hub-Signature-256: sha256=TESTE" \
  -d '{"ref":"refs/heads/main"}'
```

### Verificar status:
```bash
curl http://req.joaosmfilho.org/api/webhook/status
```

---

## Respostas

### Sucesso (200):
```json
{
  "status": "success",
  "message": "Repositório espelhado com sucesso",
  "git_output": "Already up to date.",
  "reload_triggered": true
}
```

### Erro 401:
```json
{"detail": "Assinatura inválida"}
```
→ Secret incorreto

### Erro 400:
```json
{"detail": "not main branch"}
```
→ Push em outra branch (ignorado)

---

## Segurança

O webhook usa HMAC-SHA256 para validar que as requisições vêm realmente do GitHub.

O GitHub envia no header:
```
X-Hub-Signature-256: sha256=<hmac_hash>
```

O webhook recalcula o HMAC com o secret e compara.
