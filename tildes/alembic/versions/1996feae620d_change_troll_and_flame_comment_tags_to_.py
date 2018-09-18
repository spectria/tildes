"""Change Troll and Flame comment tags to Malice

Revision ID: 1996feae620d
Revises: b825165870d9
Create Date: 2018-09-18 00:42:30.213639

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "1996feae620d"
down_revision = "b825165870d9"
branch_labels = None
depends_on = None


def upgrade():
    # ALTER TYPE doesn't work from inside a transaction, disable it
    connection = None
    if not op.get_context().as_sql:
        connection = op.get_bind()
        connection.execution_options(isolation_level="AUTOCOMMIT")

    op.execute("ALTER TYPE commenttagoption ADD VALUE IF NOT EXISTS 'MALICE'")

    # re-activate the transaction for any future migrations
    if connection is not None:
        connection.execution_options(isolation_level="READ_COMMITTED")

    # delete all "flame" tags where the user also tagged the same comment as "troll"
    # (so that we don't violate constraint when converting both to "malice")
    op.execute(
        """
        DELETE FROM comment_tags AS flame_tag
        WHERE tag = 'FLAME' AND
            EXISTS (SELECT * FROM comment_tags
                    WHERE user_id = flame_tag.user_id
                        AND comment_id = flame_tag.comment_id
                        AND tag = 'TROLL');
        """
    )

    # convert all the old "troll" and "flame" tags to "malice" ones
    op.execute("UPDATE comment_tags SET tag = 'MALICE' WHERE tag IN ('FLAME', 'TROLL')")


def downgrade():
    # not a proper revert, changing Malice back to Flame is about all we can do
    op.execute("UPDATE comment_tags SET tag = 'FLAME' WHERE tag = 'MALICE'")
