"""Add user name and collaborator user_id for auth/leave

Revision ID: 7a1b2c3d4e5f
Revises: 69b71c5b06cd
Create Date: 2026-03-09

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "7a1b2c3d4e5f"
down_revision: Union[str, None] = "69b71c5b06cd"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _column_exists(conn, table: str, column: str) -> bool:
    r = conn.execute(sa.text(f"PRAGMA table_info({table})"))
    return any(row[1] == column for row in r)


def upgrade() -> None:
    conn = op.get_bind()
    if not _column_exists(conn, "users", "name"):
        op.add_column("users", sa.Column("name", sa.String(255), nullable=True))
    with op.batch_alter_table("collaborators", schema=None) as batch_op:
        if not _column_exists(conn, "collaborators", "user_id"):
            batch_op.add_column(sa.Column("user_id", sa.Integer(), nullable=True))
        try:
            batch_op.create_foreign_key(
                "fk_collaborators_user_id",
                "users",
                ["user_id"],
                ["id"],
            )
        except Exception:
            pass  # FK may already exist


def downgrade() -> None:
    with op.batch_alter_table("collaborators", schema=None) as batch_op:
        batch_op.drop_constraint("fk_collaborators_user_id", type_="foreignkey")
        batch_op.drop_column("user_id")
    op.drop_column("users", "name")
