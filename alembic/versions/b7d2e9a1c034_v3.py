"""v3 — add read_only flag to apikey

Revision ID: b7d2e9a1c034
Revises: a3c1f82e4d56
Create Date: 2026-11-12 00:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b7d2e9a1c034"
down_revision: Union[str, Sequence[str], None] = "a3c1f82e4d56"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table("apikey") as batch_op:
        batch_op.add_column(sa.Column("read_only", sa.Boolean(), nullable=False, server_default=sa.false()))


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table("apikey") as batch_op:
        batch_op.drop_column("read_only")
