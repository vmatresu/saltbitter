"""Add messaging tables for real-time chat functionality.

Revision ID: 003
Revises: 002
Create Date: 2025-11-19 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade database schema: add messaging tables."""
    # Create blocked_users table
    op.create_table(
        "blocked_users",
        sa.Column("id", UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("blocker_user_id", UUID(as_uuid=True), nullable=False),
        sa.Column("blocked_user_id", UUID(as_uuid=True), nullable=False),
        sa.Column("blocked_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["blocker_user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["blocked_user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create indexes for blocked_users
    op.create_index("ix_blocked_users_blocker_user_id", "blocked_users", ["blocker_user_id"])
    op.create_index("ix_blocked_users_blocked_user_id", "blocked_users", ["blocked_user_id"])

    # Create message_reports table
    op.create_table(
        "message_reports",
        sa.Column("id", UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("reporter_user_id", UUID(as_uuid=True), nullable=False),
        sa.Column("reported_user_id", UUID(as_uuid=True), nullable=False),
        sa.Column("message_id", UUID(as_uuid=True), nullable=True),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False, server_default="pending"),
        sa.Column("reported_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["reporter_user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["reported_user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["message_id"], ["messages.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create indexes for message_reports
    op.create_index("ix_message_reports_reporter_user_id", "message_reports", ["reporter_user_id"])
    op.create_index("ix_message_reports_reported_user_id", "message_reports", ["reported_user_id"])
    op.create_index("ix_message_reports_reported_at", "message_reports", ["reported_at"])


def downgrade() -> None:
    """Downgrade database schema: remove messaging tables."""
    # Drop message_reports table
    op.drop_index("ix_message_reports_reported_at", table_name="message_reports")
    op.drop_index("ix_message_reports_reported_user_id", table_name="message_reports")
    op.drop_index("ix_message_reports_reporter_user_id", table_name="message_reports")
    op.drop_table("message_reports")

    # Drop blocked_users table
    op.drop_index("ix_blocked_users_blocked_user_id", table_name="blocked_users")
    op.drop_index("ix_blocked_users_blocker_user_id", table_name="blocked_users")
    op.drop_table("blocked_users")
