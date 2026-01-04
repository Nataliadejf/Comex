
-- Script SQL para MySQL Workbench
-- Banco de Dados: comex_analyzer

CREATE DATABASE IF NOT EXISTS comex_analyzer CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE comex_analyzer;

-- Tabela de operações de comércio exterior
CREATE TABLE IF NOT EXISTS operacoes_comex (
    id INT AUTO_INCREMENT PRIMARY KEY,
    ncm VARCHAR(8) NOT NULL,
    descricao_produto TEXT NOT NULL,
    tipo_operacao ENUM('IMPORTACAO', 'EXPORTACAO') NOT NULL,
    is_importacao CHAR(1) NOT NULL DEFAULT 'N',
    is_exportacao CHAR(1) NOT NULL DEFAULT 'N',
    pais_origem_destino VARCHAR(100) NOT NULL,
    uf VARCHAR(2) NOT NULL,
    porto_aeroporto VARCHAR(100),
    via_transporte ENUM('MARITIMA', 'AEREA', 'RODOVIARIA', 'FERROVIARIA', 'FLUVIAL', 'OUTRAS') NOT NULL,
    valor_fob DECIMAL(15, 2) NOT NULL,
    valor_frete DECIMAL(15, 2),
    valor_seguro DECIMAL(15, 2),
    peso_liquido_kg DECIMAL(15, 2),
    peso_bruto_kg DECIMAL(15, 2),
    quantidade_estatistica DECIMAL(15, 3),
    unidade_medida_estatistica VARCHAR(50),
    data_operacao DATE NOT NULL,
    data_importacao DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    mes_referencia VARCHAR(7) NOT NULL,
    arquivo_origem VARCHAR(255),
    INDEX idx_ncm (ncm),
    INDEX idx_tipo_operacao (tipo_operacao),
    INDEX idx_data_operacao (data_operacao),
    INDEX idx_mes_referencia (mes_referencia),
    INDEX idx_pais (pais_origem_destino),
    INDEX idx_uf (uf),
    INDEX idx_mes_tipo (mes_referencia, tipo_operacao)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Tabela de informações sobre NCMs
CREATE TABLE IF NOT EXISTS ncm_info (
    id INT AUTO_INCREMENT PRIMARY KEY,
    ncm VARCHAR(8) NOT NULL UNIQUE,
    descricao_completa TEXT,
    categoria VARCHAR(100),
    data_atualizacao DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_ncm (ncm)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Tabela de logs de coleta
CREATE TABLE IF NOT EXISTS coleta_log (
    id INT AUTO_INCREMENT PRIMARY KEY,
    mes_referencia VARCHAR(7) NOT NULL,
    tipo_operacao VARCHAR(10),
    data_inicio DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    data_fim DATETIME,
    status VARCHAR(20) NOT NULL,
    registros_coletados INT,
    erro TEXT,
    arquivo_origem VARCHAR(255),
    INDEX idx_mes_referencia (mes_referencia)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
