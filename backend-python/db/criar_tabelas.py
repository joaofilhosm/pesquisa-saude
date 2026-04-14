"""
Script para criar tabelas no Supabase via conexao direta PostgreSQL
"""
import psycopg2
from psycopg2.extensions import connection

# Configuração do Supabase
# A senha é a database password que você definiu ao criar o projeto
SUPABASE_HOST = "aws-0-us-east-1.pooler.supabase.com"
SUPABASE_DB = "postgres"
SUPABASE_USER = "postgres.xqujpkdlxvldlsqpqnkj"
# Você precisa pegar a senha no dashboard: Settings -> Database -> Database password

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

-- Tabela de referencias ABNT
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

-- Inserir fontes padrao
INSERT INTO fontes (nome, url_base, tipo, prioridade) VALUES
('Ministerio da Saude - PCDT', 'https://www.gov.br/saude/pt-br/composicao/sctie/pcdt', 'ministerio', 1),
('Biblioteca Virtual em Saude', 'https://bvsms.saude.gov.br', 'ministerio', 1),
('ANVISA', 'https://www.gov.br/anvisa/pt-br', 'ministerio', 2),
('SBMFC', 'https://www.sbmfc.org.br', 'sociedade', 2),
('Sociedade Brasileira de Pediatria', 'https://www.sbp.com.br', 'sociedade', 2),
('Sociedade Brasileira de Pneumologia e Tisiologia', 'https://sbpt.org.br', 'sociedade', 2),
('Sociedade Brasileira de Cardiologia', 'https://publicacoes.cardiol.br', 'sociedade', 2),
('HC-FMUSP', 'https://www.hcfmusp.br', 'hospital', 3),
('Hospital Sirio-Libanes', 'https://www.hospitalsiriolibanes.org.br', 'hospital', 3),
('Hospital Albert Einstein', 'https://www.einstein.br', 'hospital', 3),
('SciELO', 'https://search.scielo.org', 'base_dados', 1),
('LILACS', 'https://lilacs.bvsalud.org', 'base_dados', 1),
('PubMed', 'https://pubmed.ncbi.nlm.nih.gov', 'base_dados', 2),
('Google Academico', 'https://scholar.google.com.br', 'base_dados', 3)
ON CONFLICT (id) DO NOTHING;

-- Desabilitar RLS para desenvolvimento
ALTER TABLE artigos DISABLE ROW LEVEL SECURITY;
ALTER TABLE referencias_abnt DISABLE ROW LEVEL SECURITY;
ALTER TABLE fontes DISABLE ROW LEVEL SECURITY;
ALTER TABLE buscas_cache DISABLE ROW LEVEL SECURITY;
"""

def criar_tabelas(senha: str):
    """Cria as tabelas no Supabase"""
    try:
        # Conectar ao banco
        conn = psycopg2.connect(
            host=SUPABASE_HOST,
            database=SUPABASE_DB,
            user=SUPABASE_USER,
            password=senha,
            port=6543,  # Porta do pooler
            sslmode='require'
        )

        print("[OK] Conectado ao Supabase!")

        # Criar cursor e executar SQL
        with conn.cursor() as cur:
            print("[INFO] Executando schema SQL...")
            cur.execute(SQL_SCHEMA)
            conn.commit()
            print("[OK] Tabelas criadas com sucesso!")

        # Verificar tabelas criadas
        with conn.cursor() as cur:
            cur.execute("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_name IN ('artigos', 'referencias_abnt', 'fontes', 'buscas_cache')
                ORDER BY table_name
            """)
            tabelas = cur.fetchall()
            print(f"\n[OK] Tabelas verificadas: {[t[0] for t in tabelas]}")

        conn.close()
        return True

    except Exception as e:
        print(f"[ERRO] {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("  CRIACAO DE TABELAS - SUPABASE")
    print("=" * 60)
    print()
    print("Para encontrar a senha do banco:")
    print("1. Acesse: https://supabase.com/dashboard/project/xqujpkdlxvldlsqpqnkj")
    print("2. Settings -> Database")
    print("3. Copie a 'Database password'")
    print()

    senha = input("Cole a senha do banco: ").strip()

    if senha:
        sucesso = criar_tabelas(senha)
        if sucesso:
            print("\n[SUCESSO] Tabelas criadas! Pode iniciar a API agora.")
        else:
            print("\n[FALHA] Verifique a senha ou as configuracoes do Supabase.")
    else:
        print("\n[CANCELADO] Nenhuma senha fornecida.")
