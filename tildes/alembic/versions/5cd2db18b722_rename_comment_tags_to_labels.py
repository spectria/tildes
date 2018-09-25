"""Rename comment tags to labels

Revision ID: 5cd2db18b722
Revises: afa3128a9b54
Create Date: 2018-09-25 01:05:55.606680

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "5cd2db18b722"
down_revision = "afa3128a9b54"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("ALTER TYPE commenttagoption RENAME TO commentlabeloption")

    op.rename_table("comment_tags", "comment_labels")
    op.alter_column("comment_labels", "tag", new_column_name="label")

    op.alter_column(
        "users", "comment_tag_weight", new_column_name="comment_label_weight"
    )


def downgrade():
    op.alter_column(
        "users", "comment_label_weight", new_column_name="comment_tag_weight"
    )

    op.alter_column("comment_labels", "label", new_column_name="tag")
    op.rename_table("comment_labels", "comment_tags")

    op.execute("ALTER TYPE commentlabeloption RENAME TO commenttagoption")
