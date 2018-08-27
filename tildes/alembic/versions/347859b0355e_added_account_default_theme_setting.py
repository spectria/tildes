"""Added account default theme setting

Revision ID: 347859b0355e
Revises: 3fbddcba0e3b
Create Date: 2018-08-11 16:23:13.297883

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "347859b0355e"
down_revision = "3fbddcba0e3b"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("users", sa.Column("theme_default", sa.Text()))


def downgrade():
    op.drop_column("users", "theme_default")
