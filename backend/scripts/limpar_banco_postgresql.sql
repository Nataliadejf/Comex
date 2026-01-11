-- Script SQL para limpar o banco de dados PostgreSQL no Render
-- ⚠️ ATENÇÃO: Isso vai DELETAR TODOS OS DADOS!
-- Execute apenas se o banco está em estado inconsistente

-- 1. Limpar tabela de versão do Alembic
DROP TABLE IF EXISTS alembic_version CASCADE;

-- 2. Limpar todas as tabelas do projeto (em ordem para evitar problemas de foreign key)
DROP TABLE IF EXISTS empresas_recomendadas CASCADE;
DROP TABLE IF EXISTS cnae_hierarquia CASCADE;
DROP TABLE IF EXISTS empresas CASCADE;
DROP TABLE IF EXISTS comercio_exterior CASCADE;
DROP TABLE IF EXISTS aprovacao_cadastro CASCADE;
DROP TABLE IF EXISTS usuarios CASCADE;
DROP TABLE IF EXISTS coleta_log CASCADE;
DROP TABLE IF EXISTS ncm_info CASCADE;
DROP TABLE IF EXISTS operacoes_comex CASCADE;

-- 3. Verificar se limpou tudo
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_type = 'BASE TABLE'
ORDER BY table_name;

-- Se retornar vazio (ou apenas tabelas do sistema), está limpo!
-- Depois disso, faça deploy novamente no Render para criar tudo do zero.
