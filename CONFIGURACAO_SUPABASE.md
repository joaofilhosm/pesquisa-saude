# Configuração do Supabase

## Passo a Passo

### 1. Criar Projeto

1. Acesse https://supabase.com
2. Clique em **"Start your project"** ou **"New Project"**
3. Preencha:
   - **Name**: `pesquisa-saude` (ou outro nome)
   - **Database Password**: Escolha uma senha forte (guarde!)
   - **Region**: Escolha a mais próxima (us-east-1 para Brasil)

### 2. Executar Schema SQL

1. No dashboard do projeto, clique em **"SQL Editor"** (ícone de terminal no menu lateral)
2. Clique em **"New query"**
3. Copie e cole o conteúdo do arquivo `supabase/schema.sql`
4. Clique em **"Run"** para executar

O schema criará:
- Tabela `artigos` - Armazena artigos e protocolos
- Tabela `referencias_abnt` - Referências formatadas
- Tabela `fontes` - Fontes de pesquisa cadastradas
- Tabela `buscas_cache` - Cache de buscas
- Índices para performance

### 3. Obter Credenciais

1. No dashboard, clique em **"Settings"** (ícone de engrenagem)
2. Vá em **"API"**
3. Copie:
   - **Project URL**: `https://xxxxx.supabase.co`
   - **anon/public key**: `eyJhbG...` (chave pública)
   - **service_role key**: `eyJhbG...` (chave secreta - use no backend!)

### 4. Configurar .env

Copie as credenciais para o arquivo `.env`:

```bash
# No backend-python/
SUPABASE_URL=https://seu-projeto.supabase.co
SUPABASE_KEY=sua-chave-service-role-aqui

# No backend-node/config/
SUPABASE_URL=https://seu-projeto.supabase.co
SUPABASE_KEY=sua-chave-service-role-aqui
```

**Importante**: Use a chave `service_role` nos backends (não a anon/public).

### 5. (Opcional) Habilitar Row Level Security

Se quiser RLS, execute no SQL Editor:

```sql
-- Desabilitar RLS para desenvolvimento
ALTER TABLE artigos DISABLE ROW LEVEL SECURITY;
ALTER TABLE referencias_abnt DISABLE ROW LEVEL SECURITY;
ALTER TABLE fontes DISABLE ROW LEVEL SECURITY;
ALTER TABLE buscas_cache DISABLE ROW LEVEL SECURITY;
```

Para produção, crie políticas apropriadas.

### 6. Verificar Conexão

Após configurar, execute o teste:

```bash
python test_api.py
```

Deve mostrar:
```
✓ Node.js API: {...}
✓ Python Backend: OK
✓ Fontes: 13 fontes disponíveis
✓ Pesquisa: X resultados
```

## Custo

- **Free tier**: 500MB banco, 50k requisições/mês
- **Suficiente para**: Desenvolvimento e uso pessoal
- **Upgrade**: $25/mês para projetos maiores

## Links Úteis

- Dashboard: https://app.supabase.com
- Docs: https://supabase.com/docs
- Python Client: https://supabase.com/docs/reference/python
