"""create user devices table

Revision ID: 003
Revises: 002
Create Date: 2026-03-11
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "user_devices",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("device_token", sa.String(length=512), nullable=False),
        sa.Column(
            "platform",
            sa.Enum("ios", "android", "web", name="device_platform"),
            nullable=False,
        ),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("user_id", "device_token", name="uq_user_device_token"),
    )
    op.create_index("ix_user_devices_user_id", "user_devices", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_user_devices_user_id", table_name="user_devices")
    op.drop_table("user_devices")
    sa.Enum(name="device_platform").drop(op.get_bind(), checkfirst=True)
