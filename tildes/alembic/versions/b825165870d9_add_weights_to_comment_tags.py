"""Add weights to comment tags

Revision ID: b825165870d9
Revises: 6ede05a0ea23
Create Date: 2018-09-14 03:06:51.144073

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "b825165870d9"
down_revision = "6ede05a0ea23"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "comment_tags",
        sa.Column("weight", sa.REAL(), server_default=sa.text("1.0"), nullable=False),
    )
    op.add_column("users", sa.Column("comment_tag_weight", sa.REAL(), nullable=True))


def downgrade():
    op.drop_column("users", "comment_tag_weight")
    op.drop_column("comment_tags", "weight")
