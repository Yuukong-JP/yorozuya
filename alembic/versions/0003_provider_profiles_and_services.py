"""create provider_profiles and services

Revision ID: 0003
Revises: 0002
Create Date: 2026-06-18 03:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "provider_profiles",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("display_name", sa.String(length=100), nullable=False),
        sa.Column("profession", sa.String(length=100), nullable=False),
        sa.Column("headline", sa.String(length=200), nullable=True),
        sa.Column("bio", sa.Text(), nullable=True),
        sa.Column("phone", sa.String(length=30), nullable=True),
        sa.Column(
            "city",
            sa.String(length=100),
            server_default="Padang Panjang",
            nullable=True,
        ),
        sa.Column("area", sa.String(length=150), nullable=True),
        sa.Column("photo_url", sa.String(length=500), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_provider_profiles_id"), "provider_profiles", ["id"], unique=False
    )
    op.create_index(
        op.f("ix_provider_profiles_user_id"),
        "provider_profiles",
        ["user_id"],
        unique=True,
    )

    op.create_table(
        "services",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("provider_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=150), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("category", sa.String(length=50), nullable=False),
        sa.Column("price", sa.Integer(), nullable=False),
        sa.Column(
            "price_unit",
            sa.String(length=30),
            server_default="per pekerjaan",
            nullable=True,
        ),
        sa.Column(
            "is_active", sa.Boolean(), server_default=sa.true(), nullable=False
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["provider_id"], ["provider_profiles.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_services_id"), "services", ["id"], unique=False)
    op.create_index(
        op.f("ix_services_provider_id"), "services", ["provider_id"], unique=False
    )
    op.create_index(
        op.f("ix_services_category"), "services", ["category"], unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_services_category"), table_name="services")
    op.drop_index(op.f("ix_services_provider_id"), table_name="services")
    op.drop_index(op.f("ix_services_id"), table_name="services")
    op.drop_table("services")
    op.drop_index(
        op.f("ix_provider_profiles_user_id"), table_name="provider_profiles"
    )
    op.drop_index(op.f("ix_provider_profiles_id"), table_name="provider_profiles")
    op.drop_table("provider_profiles")
