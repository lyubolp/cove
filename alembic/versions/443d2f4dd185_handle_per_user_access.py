"""handle per-user access

Revision ID: 443d2f4dd185
Revises: f3d85ac5d377
Create Date: 2026-02-27 23:37:36.857292

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "443d2f4dd185"
down_revision: Union[str, Sequence[str], None] = "f3d85ac5d377"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = "443d2f4dd185"


def upgrade() -> None:
    """Upgrade schema."""
    op.drop_column("apikey", "access_for_project_id")

    op.create_table(
        "projectuserlink",
        sa.Column("project_id", sa.String(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["project.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("project_id", "user_id"),
    )

    op.create_table(
        "configitemuserlink",
        sa.Column("config_item_id", sa.String(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.ForeignKeyConstraint(["config_item_id"], ["configitem.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("config_item_id", "user_id"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.add_column("apikey", sa.Column("access_for_project_id", sa.String(), nullable=False))

    op.drop_table("projectuserlink")

    op.drop_table("configitemuserlink")
