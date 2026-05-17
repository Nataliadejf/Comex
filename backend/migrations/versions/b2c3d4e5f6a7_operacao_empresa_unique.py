"""operacao empresa unique periodo

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-05-17

"""
from typing import Sequence, Union

from alembic import op


revision: str = "b2c3d4e5f6a7"
down_revision: Union[str, None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        "UPDATE operacoes_empresa SET uf_destino = 'NA' WHERE uf_destino IS NULL"
    )
    op.create_unique_constraint(
        "uq_operacao_empresa_periodo",
        "operacoes_empresa",
        ["empresa_id", "tipo", "ncm", "uf_destino", "ano", "mes"],
    )


def downgrade() -> None:
    op.drop_constraint("uq_operacao_empresa_periodo", "operacoes_empresa", type_="unique")
