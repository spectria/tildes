"""Add tags to topic search vector

Revision ID: 5a7dc1032efc
Revises: 22a8ed36a3c9
Create Date: 2018-10-16 02:09:33.528836

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "5a7dc1032efc"
down_revision = "22a8ed36a3c9"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("DROP TRIGGER topic_update_search_tsv_insert ON topics")
    op.execute("DROP TRIGGER topic_update_search_tsv_update ON topics")

    op.execute(
        """
        CREATE OR REPLACE FUNCTION update_topic_search_tsv() RETURNS TRIGGER AS $$
        BEGIN
            NEW.search_tsv :=
                to_tsvector(NEW.title) ||
                to_tsvector(coalesce(NEW.markdown, '')) ||
                -- convert tags to space-separated string and replace periods with spaces
                to_tsvector(replace(array_to_string(NEW.tags, ' '), '.', ' '));

            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """
    )

    op.execute(
        """
        CREATE TRIGGER topic_update_search_tsv_insert
            BEFORE INSERT ON topics
            FOR EACH ROW
            EXECUTE PROCEDURE update_topic_search_tsv();
    """
    )

    op.execute(
        """
        CREATE TRIGGER topic_update_search_tsv_update
            BEFORE UPDATE ON topics
            FOR EACH ROW
            WHEN (
                (OLD.title IS DISTINCT FROM NEW.title)
                OR (OLD.markdown IS DISTINCT FROM NEW.markdown)
                OR (OLD.tags IS DISTINCT FROM NEW.tags)
            )
            EXECUTE PROCEDURE update_topic_search_tsv();
    """
    )

    op.execute(
        """
        UPDATE topics SET search_tsv =
            to_tsvector(title) ||
            to_tsvector(coalesce(markdown, '')) ||
            to_tsvector(replace(array_to_string(tags, ' '), '.', ' '));
    """
    )


def downgrade():
    op.execute("DROP TRIGGER topic_update_search_tsv_update ON topics")
    op.execute("DROP TRIGGER topic_update_search_tsv_insert ON topics")
    op.execute("DROP FUNCTION update_topic_search_tsv()")

    op.execute(
        """
        CREATE TRIGGER topic_update_search_tsv_insert
            BEFORE INSERT ON topics
            FOR EACH ROW
            EXECUTE PROCEDURE tsvector_update_trigger(search_tsv, 'pg_catalog.english', title, markdown);
    """
    )

    op.execute(
        """
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

    op.execute(
        """
        UPDATE topics SET search_tsv =
            to_tsvector(title) ||
            to_tsvector(coalesce(markdown, ''));
    """
    )
