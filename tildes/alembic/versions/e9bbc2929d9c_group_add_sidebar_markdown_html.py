"""Group: add sidebar markdown/html

Revision ID: e9bbc2929d9c
Revises: 9b88cb0a7b2c
Create Date: 2019-05-31 00:18:07.179045

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "e9bbc2929d9c"
down_revision = "9b88cb0a7b2c"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("groups", sa.Column("sidebar_markdown", sa.Text(), nullable=True))
    op.add_column(
        "groups", sa.Column("sidebar_rendered_html", sa.Text(), nullable=True)
    )


def downgrade():
    op.drop_column("groups", "sidebar_rendered_html")
    op.drop_column("groups", "sidebar_markdown")
