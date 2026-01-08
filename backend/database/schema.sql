-- Schema SQL para PostgreSQL
-- Este arquivo pode ser usado para criar as tabelas manualmente se necessário

-- Tabela: comex_registros (dados de comércio exterior)
CREATE TABLE IF NOT EXISTS comex_registros (
    id SERIAL PRIMARY KEY,
    ano INTEGER NOT NULL,
    mes INTEGER NOT NULL,
    tipo VARCHAR(20) NOT NULL, -- 'importacao' ou 'exportacao'
    ncm VARCHAR(20),
    descricao_ncm TEXT,
    pais VARCHAR(100),
    estado VARCHAR(2),
    valor_usd DECIMAL(15, 2) NOT NULL DEFAULT 0,
    peso_kg DECIMAL(15, 2),
    quantidade DECIMAL(15, 2),
    data DATE NOT NULL,
    mes_referencia VARCHAR(7) NOT NULL, -- 'YYYY-MM'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    arquivo_origem VARCHAR(255)
);

-- Índices para comex_registros
CREATE INDEX IF NOT EXISTS idx_comex_ano_mes ON comex_registros(ano, mes);
CREATE INDEX IF NOT EXISTS idx_comex_tipo ON comex_registros(tipo);
CREATE INDEX IF NOT EXISTS idx_comex_ncm ON comex_registros(ncm);
CREATE INDEX IF NOT EXISTS idx_comex_estado ON comex_registros(estado);
CREATE INDEX IF NOT EXISTS idx_comex_data ON comex_registros(data);
CREATE INDEX IF NOT EXISTS idx_comex_mes_ref ON comex_registros(mes_referencia);

-- Tabela: empresas
CREATE TABLE IF NOT EXISTS empresas (
    id SERIAL PRIMARY KEY,
    cnpj VARCHAR(18) UNIQUE,
    nome VARCHAR(255) NOT NULL,
    cnae VARCHAR(10),
    estado VARCHAR(2),
    tipo VARCHAR(20) NOT NULL DEFAULT 'importadora', -- 'importadora', 'exportadora', 'ambos'
    valor_importacao DECIMAL(15, 2) DEFAULT 0,
    valor_exportacao DECIMAL(15, 2) DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    arquivo_origem VARCHAR(255)
);

-- Índices para empresas
CREATE INDEX IF NOT EXISTS idx_empresas_cnpj ON empresas(cnpj);
CREATE INDEX IF NOT EXISTS idx_empresas_cnae ON empresas(cnae);
CREATE INDEX IF NOT EXISTS idx_empresas_estado ON empresas(estado);
CREATE INDEX IF NOT EXISTS idx_empresas_tipo ON empresas(tipo);
CREATE INDEX IF NOT EXISTS idx_empresas_nome ON empresas(nome);

-- Tabela: cnae_hierarquia
CREATE TABLE IF NOT EXISTS cnae_hierarquia (
    id SERIAL PRIMARY KEY,
    cnae VARCHAR(10) UNIQUE NOT NULL,
    descricao TEXT,
    setor VARCHAR(100),
    segmento VARCHAR(100),
    ramo VARCHAR(100),
    categoria VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índices para cnae_hierarquia
CREATE INDEX IF NOT EXISTS idx_cnae_setor ON cnae_hierarquia(setor);
CREATE INDEX IF NOT EXISTS idx_cnae_segmento ON cnae_hierarquia(segmento);
CREATE INDEX IF NOT EXISTS idx_cnae_ramo ON cnae_hierarquia(ramo);
CREATE INDEX IF NOT EXISTS idx_cnae_categoria ON cnae_hierarquia(categoria);
