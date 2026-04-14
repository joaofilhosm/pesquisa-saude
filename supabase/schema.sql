-- Schema do Supabase para API de Pesquisa em Saúde
-- Execute no SQL Editor do Supabase

-- Tabela de artigos e protocolos
CREATE TABLE IF NOT EXISTS artigos (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    titulo TEXT NOT NULL,
    resumo TEXT,
    autores TEXT[],
    ano INTEGER,
    fonte VARCHAR(200),
    tipo VARCHAR(50), -- 'artigo', 'protocolo', 'diretriz', 'pcdt'
    url TEXT,
    doi TEXT,
    pmid TEXT,
    keywords TEXT[],
    full_text TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Tabela de referências formatadas em ABNT
CREATE TABLE IF NOT EXISTS referencias_abnt (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    artigo_id UUID REFERENCES artigos(id) ON DELETE CASCADE,
    citacao_curta TEXT, -- Ex: (BRASIL, 2023) ou (SBMFC, 2022)
    referencia_completa TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Tabela de fontes de pesquisa
CREATE TABLE IF NOT EXISTS fontes (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    nome VARCHAR(200) NOT NULL,
    url_base TEXT NOT NULL,
    tipo VARCHAR(50), -- 'ministerio', 'sociedade', 'hospital', 'base_dados'
    ativo BOOLEAN DEFAULT true,
    prioridade INTEGER DEFAULT 1,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Tabela de buscas realizadas (cache)
CREATE TABLE IF NOT EXISTS buscas_cache (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    query TEXT NOT NULL,
    resultados UUID[] REFERENCES artigos(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Índices para performance
CREATE INDEX IF NOT EXISTS idx_artigos_titulo ON artigos USING gin(to_tsvector('portuguese', titulo));
CREATE INDEX IF NOT EXISTS idx_artigos_resumo ON artigos USING gin(to_tsvector('portuguese', resumo));
CREATE INDEX IF NOT EXISTS idx_artigos_ano ON artigos(ano);
CREATE INDEX IF NOT EXISTS idx_artigos_fonte ON artigos(fonte);
CREATE INDEX IF NOT EXISTS idx_artigos_tipo ON artigos(tipo);
CREATE INDEX IF NOT EXISTS idx_cache_query ON buscas_cache(query);

-- Inserir fontes padrão
INSERT INTO fontes (nome, url_base, tipo, prioridade) VALUES
-- Ministério da Saúde
('Ministério da Saúde - PCDT', 'https://www.gov.br/saude/pt-br/composicao/sctie/pcdt', 'ministerio', 1),
('Biblioteca Virtual em Saúde', 'https://bvsms.saude.gov.br', 'ministerio', 1),
('ANVISA', 'https://www.gov.br/anvisa/pt-br', 'ministerio', 2),

-- Sociedades Médicas
('SBMFC', 'https://www.sbmfc.org.br', 'sociedade', 2),
('Sociedade Brasileira de Pediatria', 'https://www.sbp.com.br', 'sociedade', 2),
('Sociedade Brasileira de Pneumologia e Tisiologia', 'https://sbpt.org.br', 'sociedade', 2),
('Sociedade Brasileira de Cardiologia', 'https://publicacoes.cardiol.br', 'sociedade', 2),

-- Hospitais de Referência
('HC-FMUSP', 'https://www.hcfmusp.br', 'hospital', 3),
('Hospital Sírio-Libanês', 'https://www.hospitalsiriolibanes.org.br', 'hospital', 3),
('Hospital Albert Einstein', 'https://www.einstein.br', 'hospital', 3),

-- Bases de Dados
('SciELO', 'https://search.scielo.org', 'base_dados', 1),
('LILACS', 'https://lilacs.bvsalud.org', 'base_dados', 1),
('PubMed', 'https://pubmed.ncbi.nlm.nih.gov', 'base_dados', 2),
('Google Acadêmico', 'https://scholar.google.com.br', 'base_dados', 3)
ON CONFLICT DO NOTHING;

-- Função para atualizar updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger para artigos
CREATE TRIGGER update_artigos_updated_at
    BEFORE UPDATE ON artigos
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
