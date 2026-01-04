
-- Script SQL para PostgreSQL
-- Banco de Dados: comex_analyzer

CREATE DATABASE comex_analyzer
    WITH 
    OWNER = postgres
    ENCODING = 'UTF8'
    LC_COLLATE = 'pt_BR.UTF-8'
    LC_CTYPE = 'pt_BR.UTF-8'
    TABLESPACE = pg_default
    CONNECTION LIMIT = -1;

\c comex_analyzer;

-- Criar tipos ENUM
CREATE TYPE tipo_operacao_enum AS ENUM ('IMPORTACAO', 'EXPORTACAO');
CREATE TYPE via_transporte_enum AS ENUM ('MARITIMA', 'AEREA', 'RODOVIARIA', 'FERROVIARIA', 'FLUVIAL', 'OUTRAS');

-- Tabela de operações de comércio exterior
CREATE TABLE IF NOT EXISTS operacoes_comex (
    id SERIAL PRIMARY KEY,
    ncm VARCHAR(8) NOT NULL,
    descricao_produto TEXT NOT NULL,
    tipo_operacao tipo_operacao_enum NOT NULL,
    is_importacao CHAR(1) NOT NULL DEFAULT 'N',
    is_exportacao CHAR(1) NOT NULL DEFAULT 'N',
    pais_origem_destino VARCHAR(100) NOT NULL,
    uf VARCHAR(2) NOT NULL,
    porto_aeroporto VARCHAR(100),
    via_transporte via_transporte_enum NOT NULL,
    valor_fob NUMERIC(15, 2) NOT NULL,
    valor_frete NUMERIC(15, 2),
    valor_seguro NUMERIC(15, 2),
    peso_liquido_kg NUMERIC(15, 2),
    peso_bruto_kg NUMERIC(15, 2),
    quantidade_estatistica NUMERIC(15, 3),
    unidade_medida_estatistica VARCHAR(50),
    data_operacao DATE NOT NULL,
    data_importacao TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    mes_referencia VARCHAR(7) NOT NULL,
    arquivo_origem VARCHAR(255)
);

CREATE INDEX idx_ncm ON operacoes_comex(ncm);
CREATE INDEX idx_tipo_operacao ON operacoes_comex(tipo_operacao);
CREATE INDEX idx_data_operacao ON operacoes_comex(data_operacao);
CREATE INDEX idx_mes_referencia ON operacoes_comex(mes_referencia);
CREATE INDEX idx_pais ON operacoes_comex(pais_origem_destino);
CREATE INDEX idx_uf ON operacoes_comex(uf);
CREATE INDEX idx_mes_tipo ON operacoes_comex(mes_referencia, tipo_operacao);

-- Tabela de informações sobre NCMs
CREATE TABLE IF NOT EXISTS ncm_info (
    id SERIAL PRIMARY KEY,
    ncm VARCHAR(8) NOT NULL UNIQUE,
    descricao_completa TEXT,
    categoria VARCHAR(100),
    data_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_ncm_info ON ncm_info(ncm);

-- Tabela de logs de coleta
CREATE TABLE IF NOT EXISTS coleta_log (
    id SERIAL PRIMARY KEY,
    mes_referencia VARCHAR(7) NOT NULL,
    tipo_operacao VARCHAR(10),
    data_inicio TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    data_fim TIMESTAMP,
    status VARCHAR(20) NOT NULL,
    registros_coletados INTEGER,
    erro TEXT,
    arquivo_origem VARCHAR(255)
);

CREATE INDEX idx_mes_referencia_log ON coleta_log(mes_referencia);
