"""Initial schema for encuestas, catalogo_comunidades, and respuestas_ciudadanas.

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-11-18 13:35:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0001_initial_schema"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "catalogo_comunidades",
        sa.Column("codigo", sa.String(length=20), nullable=False),
        sa.Column("nombre", sa.String(length=150), nullable=False),
        sa.Column("xpar", sa.String(length=10), nullable=False),
        sa.Column("parroquia", sa.String(length=60), nullable=False),
        sa.Column("municipio_codigo", sa.String(length=10), nullable=False),
        sa.Column("municipio", sa.String(length=60), nullable=False),
        sa.PrimaryKeyConstraint("codigo"),
    )
    op.create_index(
        "ix_catalogo_comunidades_nombre",
        "catalogo_comunidades",
        ["nombre"],
        unique=False,
    )
    op.create_index(
        "ix_catalogo_comunidades_xpar",
        "catalogo_comunidades",
        ["xpar"],
        unique=False,
    )
    op.create_index(
        "ix_catalogo_comunidades_parroquia",
        "catalogo_comunidades",
        ["parroquia"],
        unique=False,
    )

    op.create_table(
        "encuestas",
        sa.Column(
            "id",
            sa.CHAR(length=36).with_variant(postgresql.UUID(as_uuid=True), "postgresql"),
            nullable=False,
        ),
        sa.Column("titulo", sa.String(length=255), nullable=False),
        sa.Column("slug", sa.String(length=120), nullable=False),
        sa.Column("tipo_instrumento", sa.String(length=30), nullable=False),
        sa.Column(
            "esquema_formio",
            sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), "postgresql"),
            nullable=False,
        ),
        sa.Column("activa", sa.Boolean(), nullable=False),
        sa.Column(
            "creado_en",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_encuestas_slug", "encuestas", ["slug"], unique=True)

    op.create_table(
        "respuestas_ciudadanas",
        sa.Column(
            "id",
            sa.BigInteger().with_variant(sa.Integer(), "sqlite"),
            autoincrement=True,
            nullable=False,
        ),
        sa.Column(
            "encuesta_id",
            sa.CHAR(length=36).with_variant(postgresql.UUID(as_uuid=True), "postgresql"),
            nullable=False,
        ),
        sa.Column(
            "client_submission_id",
            sa.CHAR(length=36).with_variant(postgresql.UUID(as_uuid=True), "postgresql"),
            nullable=True,
        ),
        sa.Column("cedula", sa.String(length=15), nullable=True),
        sa.Column("parroquia", sa.String(length=60), nullable=False),
        sa.Column("comunidad_codigo", sa.String(length=20), nullable=True),
        sa.Column("zona_od", sa.String(length=30), nullable=True),
        sa.Column(
            "datos",
            sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), "postgresql"),
            nullable=False,
        ),
        sa.Column(
            "fecha_registro",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["encuesta_id"], ["encuestas.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["comunidad_codigo"],
            ["catalogo_comunidades.codigo"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("encuesta_id", "cedula", name="uq_voto_ciudadano"),
    )
    op.create_index(
        "ix_respuestas_ciudadanas_client_submission_id",
        "respuestas_ciudadanas",
        ["client_submission_id"],
        unique=True,
    )
    op.create_index(
        "ix_respuestas_ciudadanas_comunidad_codigo",
        "respuestas_ciudadanas",
        ["comunidad_codigo"],
        unique=False,
    )
    op.create_index(
        "ix_respuestas_ciudadanas_encuesta_id",
        "respuestas_ciudadanas",
        ["encuesta_id"],
        unique=False,
    )
    op.create_index(
        "ix_respuestas_ciudadanas_parroquia",
        "respuestas_ciudadanas",
        ["parroquia"],
        unique=False,
    )
    op.create_index(
        "ix_respuestas_ciudadanas_zona_od",
        "respuestas_ciudadanas",
        ["zona_od"],
        unique=False,
    )

    if op.get_context().dialect.name == "postgresql":
        op.create_index(
            "idx_respuestas_datos_gin",
            "respuestas_ciudadanas",
            ["datos"],
            unique=False,
            postgresql_using="gin",
            postgresql_ops={"datos": "jsonb_path_ops"},
        )
        op.create_index(
            "idx_respuestas_encuesta_parroquia",
            "respuestas_ciudadanas",
            ["encuesta_id", "parroquia"],
            unique=False,
        )
        op.create_index(
            "idx_respuestas_encuesta_zona_od",
            "respuestas_ciudadanas",
            ["encuesta_id", "zona_od"],
            unique=False,
        )


def downgrade() -> None:
    if op.get_context().dialect.name == "postgresql":
        op.drop_index("idx_respuestas_encuesta_zona_od", table_name="respuestas_ciudadanas")
        op.drop_index("idx_respuestas_encuesta_parroquia", table_name="respuestas_ciudadanas")
        op.drop_index("idx_respuestas_datos_gin", table_name="respuestas_ciudadanas")

    op.drop_index("ix_respuestas_ciudadanas_zona_od", table_name="respuestas_ciudadanas")
    op.drop_index("ix_respuestas_ciudadanas_parroquia", table_name="respuestas_ciudadanas")
    op.drop_index("ix_respuestas_ciudadanas_encuesta_id", table_name="respuestas_ciudadanas")
    op.drop_index(
        "ix_respuestas_ciudadanas_comunidad_codigo",
        table_name="respuestas_ciudadanas",
    )
    op.drop_index(
        "ix_respuestas_ciudadanas_client_submission_id",
        table_name="respuestas_ciudadanas",
    )
    op.drop_table("respuestas_ciudadanas")

    op.drop_index("ix_encuestas_slug", table_name="encuestas")
    op.drop_table("encuestas")

    op.drop_index("ix_catalogo_comunidades_parroquia", table_name="catalogo_comunidades")
    op.drop_index("ix_catalogo_comunidades_xpar", table_name="catalogo_comunidades")
    op.drop_index("ix_catalogo_comunidades_nombre", table_name="catalogo_comunidades")
    op.drop_table("catalogo_comunidades")
