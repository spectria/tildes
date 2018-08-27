"""Drop removed_time column from comments

Revision ID: b424479202f9
Revises: 347859b0355e
Create Date: 2018-08-27 21:08:06.656876

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "b424479202f9"
down_revision = "347859b0355e"
branch_labels = None
depends_on = None


def upgrade():
    op.drop_column("comments", "removed_time")

    op.execute("DROP TRIGGER remove_comment_set_removed_time_update ON comments")
    op.execute("DROP FUNCTION set_comment_removed_time")


def downgrade():
    op.add_column(
        "comments",
        sa.Column(
            "removed_time",
            postgresql.TIMESTAMP(timezone=True),
            autoincrement=False,
            nullable=True,
        ),
    )

    op.execute(
        """
        CREATE OR REPLACE FUNCTION set_comment_removed_time() RETURNS TRIGGER AS $$
        BEGIN
            IF (NEW.is_removed = TRUE) THEN
                NEW.removed_time := current_timestamp;
            ELSE
                NEW.removed_time := NULL;
            END IF;

            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;

        CREATE TRIGGER remove_comment_set_removed_time_update
            BEFORE UPDATE ON comments
            FOR EACH ROW
            WHEN (OLD.is_removed IS DISTINCT FROM NEW.is_removed)
            EXECUTE PROCEDURE set_comment_removed_time();
    """
    )
