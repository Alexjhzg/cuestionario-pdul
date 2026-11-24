"""Widen respuestas_ciudadanas.zona_od from String(30) to String(120) for free-text O-D zones.

Revision ID: 0002_widen_zona_od
Revises: 0001_initial_schema
Create Date: 2026-11-24 09:20:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0002_widen_zona_od"
down_revision: Union[str, None] = "0001_initial_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("respuestas_ciudadanas") as batch_op:
        batch_op.alter_column(
            "zona_od",
            existing_type=sa.String(length=30),
            type_=sa.String(length=120),
            existing_nullable=True,
        )


def downgrade() -> None:
    with op.batch_alter_table("respuestas_ciudadanas") as batch_op:
        batch_op.alter_column(
            "zona_od",
            existing_type=sa.String(length=120),
            type_=sa.String(length=30),
            existing_nullable=True,
        )

