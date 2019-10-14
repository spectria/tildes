"""Add search column/index for comments

Revision ID: 679090fd4977
Revises: 9fc0033a2b61
Create Date: 2019-10-12 17:46:13.418316

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "679090fd4977"
down_revision = "9fc0033a2b61"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "comments", sa.Column("search_tsv", postgresql.TSVECTOR(), nullable=True)
    )
    op.create_index(
        "ix_comments_search_tsv_gin",
        "comments",
        ["search_tsv"],
        unique=False,
        postgresql_using="gin",
    )

    op.execute(
        """
        CREATE TRIGGER comment_update_search_tsv_insert
            BEFORE INSERT ON comments
            FOR EACH ROW
            EXECUTE PROCEDURE tsvector_update_trigger(search_tsv, 'pg_catalog.english', markdown);

        CREATE TRIGGER comment_update_search_tsv_update
            BEFORE UPDATE ON comments
            FOR EACH ROW
            WHEN (OLD.markdown IS DISTINCT FROM NEW.markdown)
            EXECUTE PROCEDURE tsvector_update_trigger(search_tsv, 'pg_catalog.english', markdown);
    """
    )

    # increase the timeout since updating search for all comments could take a while
    op.execute("SET statement_timeout TO '10min'")
    op.execute(
        "UPDATE comments SET search_tsv = to_tsvector('pg_catalog.english', markdown)"
    )


def downgrade():
    op.drop_index("ix_comments_search_tsv_gin", table_name="comments")
    op.drop_column("comments", "search_tsv")
