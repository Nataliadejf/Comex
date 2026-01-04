"""
Script para configurar banco de dados MySQL/PostgreSQL usando Workbench.
Permite migrar de SQLite para MySQL/PostgreSQL.
"""
import sys
from pathlib import Path

backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from loguru import logger
from config import settings


def gerar_sql_create_tables():
    """Gera SQL para criar tabelas no MySQL/PostgreSQL."""
    
    sql_mysql = """
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
"""
    
    sql_postgresql = """
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

\\c comex_analyzer;

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
"""
    
    return sql_mysql, sql_postgresql


def main():
    """Gera scripts SQL para configuração do banco."""
    logger.info("=" * 60)
    logger.info("GERADOR DE SCRIPTS SQL - MYSQL/POSTGRESQL")
    logger.info("=" * 60)
    logger.info("")
    
    sql_mysql, sql_postgresql = gerar_sql_create_tables()
    
    # Salvar scripts
    scripts_dir = Path(__file__).parent.parent / "scripts" / "sql"
    scripts_dir.mkdir(parents=True, exist_ok=True)
    
    # MySQL
    mysql_file = scripts_dir / "create_tables_mysql.sql"
    mysql_file.write_text(sql_mysql, encoding='utf-8')
    logger.info(f"✅ Script MySQL criado: {mysql_file}")
    
    # PostgreSQL
    postgres_file = scripts_dir / "create_tables_postgresql.sql"
    postgres_file.write_text(sql_postgresql, encoding='utf-8')
    logger.info(f"✅ Script PostgreSQL criado: {postgres_file}")
    
    logger.info("")
    logger.info("=" * 60)
    logger.info("INSTRUÇÕES:")
    logger.info("=" * 60)
    logger.info("")
    logger.info("MYSQL WORKBENCH:")
    logger.info("   1. Abra o MySQL Workbench")
    logger.info("   2. Conecte ao servidor MySQL")
    logger.info("   3. Abra o arquivo: scripts/sql/create_tables_mysql.sql")
    logger.info("   4. Execute o script (Ctrl+Shift+Enter)")
    logger.info("   5. Configure no .env:")
    logger.info("      DATABASE_URL=mysql+pymysql://usuario:senha@localhost:3306/comex_analyzer")
    logger.info("")
    logger.info("POSTGRESQL:")
    logger.info("   1. Conecte ao PostgreSQL")
    logger.info("   2. Execute: psql -U postgres -f scripts/sql/create_tables_postgresql.sql")
    logger.info("   3. Configure no .env:")
    logger.info("      DATABASE_URL=postgresql://usuario:senha@localhost:5432/comex_analyzer")
    logger.info("")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()



