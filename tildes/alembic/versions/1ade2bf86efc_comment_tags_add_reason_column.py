"""comment_tags: add reason column

Revision ID: 1ade2bf86efc
Revises: 1996feae620d
Create Date: 2018-09-18 20:44:19.357105

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "1ade2bf86efc"
down_revision = "1996feae620d"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("comment_tags", sa.Column("reason", sa.Text(), nullable=True))


def downgrade():
    op.drop_column("comment_tags", "reason")
