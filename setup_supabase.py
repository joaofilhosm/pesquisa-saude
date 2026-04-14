"""
Script para configurar o Supabase - criar tabelas e inserir fontes
"""
import httpx
import json

SUPABASE_URL = "https://xqujpkdlxvldlsqpqnkj.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InhxdWpwa2RseHZsZGxzcXBxbmtqIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3NjExMzUxOCwiZXhwIjoyMDkxNjg5NTE4fQ.UMMm0A5qM2It_Zd6A9OXehOw9E_i3JXjmrKRJSKUQBc"

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation"
}

# SQL para criar as tabelas
SQL_SCHEMA = """
-- Tabela de artigos
CREATE TABLE IF NOT EXISTS artigos (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    titulo TEXT NOT NULL,
    resumo TEXT,
    autores TEXT[],
    ano INTEGER,
    fonte VARCHAR(200),
    tipo VARCHAR(50),
    url TEXT,
    doi TEXT,
    pmid TEXT,
    keywords TEXT[],
    full_text TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Tabela de referências ABNT
CREATE TABLE IF NOT EXISTS referencias_abnt (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    artigo_id UUID REFERENCES artigos(id) ON DELETE CASCADE,
    citacao_curta TEXT,
    referencia_completa TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Tabela de fontes
CREATE TABLE IF NOT EXISTS fontes (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    nome VARCHAR(200) NOT NULL,
    url_base TEXT NOT NULL,
    tipo VARCHAR(50),
    ativo BOOLEAN DEFAULT true,
    prioridade INTEGER DEFAULT 1,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Tabela de cache
CREATE TABLE IF NOT EXISTS buscas_cache (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    query TEXT NOT NULL,
    resultados UUID[],
    created_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ DEFAULT NOW()
);
"""

def executar_sql(sql: str):
    """Executa SQL via API do Supabase"""
    url = f"{SUPABASE_URL}/rest/v1/"

    # Primeiro tentamos verificar se as tabelas existem
    response = httpx.get(
        f"{url}fontes",
        headers=headers,
        params={"limit": "1"}
    )

    if response.status_code == 200:
        print("[OK] Tabela 'fontes' ja existe!")
        return True
    elif "PGRST205" in response.text:
        print("[AVISO] Tabelas nao existem. Executando schema...")
        print("  -> Acesse o dashboard do Supabase -> SQL Editor")
        print("  -> Copie e execute o conteudo do arquivo: supabase/schema_completo.sql")
        return False
    else:
        print(f"Erro: {response.status_code} - {response.text}")
        return False

def verificar_tabelas():
    """Verifica se todas as tabelas foram criadas"""
    tabelas = ["artigos", "referencias_abnt", "fontes", "buscas_cache"]
    criadas = []

    for tabela in tabelas:
        response = httpx.get(
            f"{SUPABASE_URL}/rest/v1/{tabela}",
            headers=headers,
            params={"limit": "0"}
        )
        if response.status_code == 200:
            criadas.append(tabela)
            print(f"[OK] Tabela '{tabela}' OK")
        else:
            print(f"[ERRO] Tabela '{tabela}' NAO encontrada")

    return len(criadas) == len(tabelas)

if __name__ == "__main__":
    print("=" * 60)
    print("  VERIFICACAO DO SCHEMA - SUPABASE")
    print("=" * 60)
    print()

    todas_ok = verificar_tabelas()

    print()
    if todas_ok:
        print("[SUCESSO] Todas as tabelas foram criadas!")
    else:
        print("[AVISO] Algumas tabelas estao faltando.")
        print()
        print("PARA CRIAR AS TABELAS:")
        print("1. Acesse: https://supabase.com/dashboard/project/xqujpkdlxvldlsqpqnkj/sql")
        print("2. Clique em 'New query'")
        print("3. Copie TODO o conteudo do arquivo: supabase/schema_completo.sql")
        print("4. Cole no editor e clique em 'Run' (Ctrl+Enter)")
        print()
