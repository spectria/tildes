"""Rename group_wiki_pages.slug to path

Revision ID: f20ce28b1d5c
Revises: cddd7d7ed0ea
Create Date: 2019-08-10 04:40:04.657360

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "f20ce28b1d5c"
down_revision = "cddd7d7ed0ea"
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column("group_wiki_pages", "slug", new_column_name="path")


def downgrade():
    op.alter_column("group_wiki_pages", "path", new_column_name="slug")
