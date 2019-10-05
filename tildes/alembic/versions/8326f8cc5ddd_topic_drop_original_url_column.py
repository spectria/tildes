"""Topic: drop original_url column

Revision ID: 8326f8cc5ddd
Revises: 20b5f07e5f80
Create Date: 2019-10-05 00:52:20.515858

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "8326f8cc5ddd"
down_revision = "20b5f07e5f80"
branch_labels = None
depends_on = None


def upgrade():
    op.drop_column("topics", "original_url")


def downgrade():
    op.add_column("topics", sa.Column("original_url", sa.Text(), nullable=True))
