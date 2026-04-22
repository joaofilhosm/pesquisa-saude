#!/bin/bash
# Teste das APIs Google Scholar via endpoint da API
# As chaves devem estar configuradas no repo-panel

API_URL="${API_URL:-http://localhost:8001}"
API_KEY="${API_KEY:-sk-pesquisa-saude-2026-master-key}"

echo "============================================================"
echo "TESTE DAS APIs GOOGLE SCHOLAR VIA ENDPOINT"
echo "============================================================"
echo "API URL: $API_URL"
echo "API Key: $API_KEY"
echo ""

# Função para testar uma fonte
testar_fonte() {
    local fonte=$1
    local nome=$2

    echo "------------------------------------------------------------"
    echo "🔵 TESTANDO: $nome ($fonte)"
    echo "------------------------------------------------------------"

    response=$(curl -s -w "\n%{http_code}" -X POST "$API_URL/pesquisar" \
        -H "X-API-Key: $API_KEY" \
        -H "Content-Type: application/json" \
        -d "{\"query\": \"diabetes tipo 2\", \"fontes\": [\"$fonte\"], \"limit\": 3}")

    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | head -n-1)

    echo "HTTP Status: $http_code"

    if [ "$http_code" = "200" ]; then
        total=$(echo "$body" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('total',0))" 2>/dev/null || echo "?")
        echo "✅ Sucesso! Resultados: $total"

        # Mostra primeiro resultado se existir
        echo "$body" | python3 -c "
import sys, json
d = json.load(sys.stdin)
if d.get('resultados'):
    r = d['resultados'][0]
    print(f\"   Título: {r['titulo'][:60]}...\")
    print(f\"   Ano: {r.get('ano', 'N/A')}\")
    print(f\"   Fonte: {r.get('fonte', 'N/A')}\")
    if r.get('url'): print(f\"   URL: {r['url'][:50]}...\")
    if r.get('doi'): print(f\"   DOI: {r['doi']}\")
" 2>/dev/null
    else
        echo "❌ Erro:"
        echo "$body" | python3 -c "import sys,json; d=json.load(sys.stdin); print(f\"   {d.get('detail', 'Erro desconhecido')}\")" 2>/dev/null || echo "$body"
    fi
    echo ""
}

# Testa cada API individualmente
testar_fonte "serpapi" "SerpAPI"
testar_fonte "searchapi" "SearchApi.io"
testar_fonte "scholarapi" "ScholarAPI.net"
testar_fonte "serply" "Serply.io"

echo "============================================================"
echo "✅ TESTES CONCLUÍDOS"
echo "============================================================"
