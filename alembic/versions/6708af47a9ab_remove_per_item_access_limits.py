"""Remove per-item access limits

Revision ID: 6708af47a9ab
Revises: 443d2f4dd185
Create Date: 2026-03-06 17:56:30.494617

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "6708af47a9ab"
down_revision: Union[str, Sequence[str], None] = "443d2f4dd185"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.drop_table("configitemuserlink")


def downgrade() -> None:
    """Downgrade schema."""
    op.create_table(
        "configitemuserlink",
        sa.Column("config_item_id", sa.String(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.ForeignKeyConstraint(["config_item_id"], ["configitem.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("config_item_id", "user_id"),
    )
