"""Add suggestion_votes table for one vote per user per suggestion

Revision ID: 8b2c3d4e5f6a
Revises: 7a1b2c3d4e5f
Create Date: 2026-03-09

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "8b2c3d4e5f6a"
down_revision: Union[str, None] = "7a1b2c3d4e5f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "suggestion_votes",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("suggestion_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["suggestion_id"], ["suggestions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("suggestion_id", "user_id", name="uq_suggestion_user"),
    )


def downgrade() -> None:
    op.drop_table("suggestion_votes")
