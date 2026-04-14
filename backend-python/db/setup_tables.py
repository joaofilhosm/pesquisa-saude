"""
Script para criar tabelas no Supabase via Python
Usa a biblioteca supabase para executar SQL
"""
import os
from supabase import create_client

# Configuração
SUPABASE_URL = "https://xqujpkdlxvldlsqpqnkj.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InhxdWpwa2RseHZsZGxzcXBxbmtqIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3NjExMzUxOCwiZXhwIjoyMDkxNjg5NTE4fQ.UMMm0A5qM2It_Zd6A9OXehOw9E_i3JXjmrKRJSKUQBc"

# Criar cliente
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# SQL para criar tabelas
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

-- Desabilitar RLS
ALTER TABLE artigos DISABLE ROW LEVEL SECURITY;
ALTER TABLE referencias_abnt DISABLE ROW LEVEL SECURITY;
ALTER TABLE fontes DISABLE ROW LEVEL SECURITY;
ALTER TABLE buscas_cache DISABLE ROW LEVEL SECURITY;
"""

def main():
    print("=" * 60)
    print("  CRIACAO DE TABELAS - SUPABASE")
    print("=" * 60)
    print()

    # Infelizmente, a biblioteca Python do Supabase tambem nao executa SQL arbitrário
    # Precisamos usar a API de Database do Supabase

    print("[INFO] A API do Supabase requer execucao de SQL via dashboard.")
    print()
    print("Siga estes passos:")
    print()
    print("1. Acesse: https://supabase.com/dashboard/project/xqujpkdlxvldlsqpqnkj/sql")
    print("2. Clique em 'New query'")
    print("3. Copie o SQL abaixo e cole no editor")
    print("4. Clique em 'Run' (Ctrl+Enter)")
    print()
    print("-" * 60)
    print(SQL_SCHEMA)
    print("-" * 60)

if __name__ == "__main__":
    main()
