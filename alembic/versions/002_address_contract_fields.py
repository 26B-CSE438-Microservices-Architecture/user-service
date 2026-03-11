"""add address contract fields

Revision ID: 002
Revises: 001
Create Date: 2026-03-11
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column("addresses", "label", existing_type=sa.String(length=100), nullable=True)
    op.alter_column("addresses", "postal_code", existing_type=sa.String(length=10), nullable=True)

    op.add_column(
        "addresses",
        sa.Column("address_title", sa.String(length=100), nullable=False, server_default=""),
    )
    op.add_column(
        "addresses",
        sa.Column("district", sa.String(length=100), nullable=False, server_default=""),
    )
    op.add_column(
        "addresses",
        sa.Column("neighborhood", sa.String(length=120), nullable=False, server_default=""),
    )
    op.add_column(
        "addresses",
        sa.Column("building_no", sa.String(length=20), nullable=False, server_default=""),
    )
    op.add_column(
        "addresses",
        sa.Column("floor", sa.String(length=20), nullable=False, server_default=""),
    )
    op.add_column(
        "addresses",
        sa.Column("apartment_no", sa.String(length=20), nullable=False, server_default=""),
    )
    op.add_column(
        "addresses",
        sa.Column("address_description", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "addresses",
        sa.Column("phone", sa.String(length=20), nullable=False, server_default=""),
    )
    op.add_column(
        "addresses",
        sa.Column(
            "is_current",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )

    op.alter_column("addresses", "address_title", server_default=None)
    op.alter_column("addresses", "district", server_default=None)
    op.alter_column("addresses", "neighborhood", server_default=None)
    op.alter_column("addresses", "building_no", server_default=None)
    op.alter_column("addresses", "floor", server_default=None)
    op.alter_column("addresses", "apartment_no", server_default=None)
    op.alter_column("addresses", "phone", server_default=None)
    op.alter_column("addresses", "is_current", server_default=None)


def downgrade() -> None:
    op.drop_column("addresses", "is_current")
    op.drop_column("addresses", "phone")
    op.drop_column("addresses", "address_description")
    op.drop_column("addresses", "apartment_no")
    op.drop_column("addresses", "floor")
    op.drop_column("addresses", "building_no")
    op.drop_column("addresses", "neighborhood")
    op.drop_column("addresses", "district")
    op.drop_column("addresses", "address_title")

    op.alter_column("addresses", "postal_code", existing_type=sa.String(length=10), nullable=False)
    op.alter_column("addresses", "label", existing_type=sa.String(length=100), nullable=False)
