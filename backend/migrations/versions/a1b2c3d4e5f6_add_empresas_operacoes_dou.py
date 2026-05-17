"""add empresas operacoes dou ncm cache

Revision ID: a1b2c3d4e5f6
Revises: de31743c9111
Create Date: 2026-05-17

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = "de31743c9111"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "operacoes_empresa",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("empresa_id", sa.Integer(), nullable=False),
        sa.Column("tipo", sa.String(length=3), nullable=False),
        sa.Column("ncm", sa.String(length=8), nullable=False),
        sa.Column("ncm_descricao", sa.Text(), nullable=True),
        sa.Column("uf_origem", sa.String(length=2), nullable=True),
        sa.Column("uf_destino", sa.String(length=2), nullable=True),
        sa.Column("pais", sa.String(length=60), nullable=True),
        sa.Column("ano", sa.Integer(), nullable=True),
        sa.Column("mes", sa.Integer(), nullable=True),
        sa.Column("valor_usd", sa.Numeric(18, 2), nullable=True),
        sa.Column("peso_kg", sa.Numeric(18, 3), nullable=True),
        sa.Column("quantidade", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["empresa_id"], ["empresas.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_operacoes_empresa_empresa_id", "operacoes_empresa", ["empresa_id"])
    op.create_index("ix_operacoes_empresa_ncm", "operacoes_empresa", ["ncm"])
    op.create_index("idx_op_emp_empresa_tipo", "operacoes_empresa", ["empresa_id", "tipo"])
    op.create_index("idx_op_emp_ncm_ano", "operacoes_empresa", ["ncm", "ano"])

    op.create_table(
        "dou_registros",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("cnpj", sa.String(length=18), nullable=True),
        sa.Column("razao_social", sa.String(length=255), nullable=True),
        sa.Column("data_pub", sa.Date(), nullable=True),
        sa.Column("secao", sa.String(length=10), nullable=True),
        sa.Column("tipo_ato", sa.String(length=100), nullable=True),
        sa.Column("resumo", sa.Text(), nullable=True),
        sa.Column("url", sa.Text(), nullable=True),
        sa.Column("scraped_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_dou_registros_cnpj", "dou_registros", ["cnpj"])
    op.create_index("idx_dou_cnpj_data", "dou_registros", ["cnpj", "data_pub"])

    op.create_table(
        "ncm_descricao",
        sa.Column("ncm", sa.String(length=8), nullable=False),
        sa.Column("descricao_tec", sa.Text(), nullable=True),
        sa.Column("sugestao_produto", sa.Text(), nullable=True),
        sa.Column("atualizado_em", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("ncm"),
    )


def downgrade() -> None:
    op.drop_table("ncm_descricao")
    op.drop_table("dou_registros")
    op.drop_table("operacoes_empresa")
