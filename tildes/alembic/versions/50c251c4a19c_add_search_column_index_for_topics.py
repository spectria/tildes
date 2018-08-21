"""Add search column/index for topics

Revision ID: 50c251c4a19c
Revises: d33fb803a153
Create Date: 2018-08-20 19:18:04.129255

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "50c251c4a19c"
down_revision = "d33fb803a153"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "topics", sa.Column("search_tsv", postgresql.TSVECTOR(), nullable=True)
    )
    op.create_index(
        "ix_topics_search_tsv_gin",
        "topics",
        ["search_tsv"],
        unique=False,
        postgresql_using="gin",
    )

    op.execute(
        """
        UPDATE topics
        SET search_tsv = to_tsvector('pg_catalog.english', title)
                || to_tsvector('pg_catalog.english', COALESCE(markdown, ''));
    """
    )

    op.execute(
        """
        CREATE TRIGGER topic_update_search_tsv_insert
            BEFORE INSERT ON topics
            FOR EACH ROW
            EXECUTE PROCEDURE tsvector_update_trigger(search_tsv, 'pg_catalog.english', title, markdown);

        CREATE TRIGGER topic_update_search_tsv_update
            BEFORE UPDATE ON topics
            FOR EACH ROW
            WHEN (
                (OLD.title IS DISTINCT FROM NEW.title)
                OR (OLD.markdown IS DISTINCT FROM NEW.markdown)
            )
            EXECUTE PROCEDURE tsvector_update_trigger(search_tsv, 'pg_catalog.english', title, markdown);
    """
    )


def downgrade():
    op.drop_index("ix_topics_search_tsv_gin", table_name="topics")
    op.drop_column("topics", "search_tsv")

    op.execute("DROP TRIGGER topic_update_search_tsv_insert ON topics")
    op.execute("DROP TRIGGER topic_update_search_tsv_update ON topics")
