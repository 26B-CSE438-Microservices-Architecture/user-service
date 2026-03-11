"""split user name and surname

Revision ID: 004
Revises: 003
Create Date: 2026-03-11
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "004"
down_revision: Union[str, None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("surname", sa.String(length=255), nullable=False, server_default=""),
    )

    op.execute(
        """
        UPDATE users
        SET
            name = split_part(trim(name), ' ', 1),
            surname = CASE
                WHEN position(' ' in trim(name)) > 0
                    THEN ltrim(substr(trim(name), position(' ' in trim(name)) + 1))
                ELSE ''
            END
        """
    )

    op.alter_column("users", "surname", server_default=None)


def downgrade() -> None:
    op.execute(
        """
        UPDATE users
        SET name = trim(
            CASE
                WHEN coalesce(surname, '') = '' THEN name
                ELSE name || ' ' || surname
            END
        )
        """
    )
    op.drop_column("users", "surname")
