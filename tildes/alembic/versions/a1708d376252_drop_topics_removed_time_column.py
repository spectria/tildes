"""Drop topics.removed_time column

Revision ID: a1708d376252
Revises: bcf1406bb6c5
Create Date: 2018-08-23 00:29:41.024890

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "a1708d376252"
down_revision = "bcf1406bb6c5"
branch_labels = None
depends_on = None


def upgrade():
    op.drop_column("topics", "removed_time")


def downgrade():
    op.add_column(
        "topics",
        sa.Column(
            "removed_time",
            postgresql.TIMESTAMP(timezone=True),
            autoincrement=False,
            nullable=True,
        ),
    )
