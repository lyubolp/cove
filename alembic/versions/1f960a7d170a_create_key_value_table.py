"""create key-value table

Revision ID: 1f960a7d170a
Revises:
Create Date: 2026-02-22 09:29:22.020724

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "1f960a7d170a"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    project_table = op.create_table(
        "project",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    op.bulk_insert(project_table, [{"id": "1234", "name": "Default Project"}])

    keyvalue_table = op.create_table(
        "keyvalue",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("project_id", sa.String(), nullable=False),
        sa.Column("key", sa.String(), nullable=False),
        sa.Column("value", sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["project_id"], ["project.id"], ondelete="CASCADE"),
    )
    op.bulk_insert(keyvalue_table, [{"id": "123", "project_id": "1234", "key": "hello", "value": "world"}])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("keyvalue")
    op.drop_table("project")
