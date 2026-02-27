"""add auth tables

Revision ID: 1f960a7d170a
Revises:
Create Date: 2026-02-22 09:29:22.020724

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "f3d85ac5d377"
down_revision: Union[str, Sequence[str], None] = "1f960a7d170a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: str = "1f960a7d170a"


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("project", sa.Column("is_public", sa.Boolean(), nullable=False, server_default="false"))
    op.add_column("keyvalue", sa.Column("is_public", sa.Boolean(), nullable=False, server_default="false"))

    op.create_table(
        "user",
        sa.Column("id", sa.String(), primary_key=True, nullable=False),
        sa.Column("username", sa.String(), nullable=False),
        sa.Column("password_hash", sa.String(), nullable=False),
    )

    op.create_table(
        "apikey",
        sa.Column("id", sa.String(), primary_key=True, nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("key", sa.String(), nullable=False),
        sa.Column("access_for_project_id", sa.String(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["access_for_project_id"], ["project.id"], ondelete="CASCADE"),
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.drop_column("keyvalue", "is_public")
    op.drop_column("project", "is_public")

    op.drop_table("apikey")
    op.drop_table("user")
