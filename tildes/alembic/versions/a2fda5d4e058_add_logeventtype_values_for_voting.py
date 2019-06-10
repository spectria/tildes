"""Add logeventtype values for voting

Revision ID: a2fda5d4e058
Revises: e9bbc2929d9c
Create Date: 2019-06-10 17:56:11.892793

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "a2fda5d4e058"
down_revision = "e9bbc2929d9c"
branch_labels = None
depends_on = None


def upgrade():
    # ALTER TYPE doesn't work from inside a transaction, disable it
    connection = None
    if not op.get_context().as_sql:
        connection = op.get_bind()
        connection.execution_options(isolation_level="AUTOCOMMIT")

    op.execute("ALTER TYPE logeventtype ADD VALUE IF NOT EXISTS 'COMMENT_VOTE'")
    op.execute("ALTER TYPE logeventtype ADD VALUE IF NOT EXISTS 'COMMENT_UNVOTE'")
    op.execute("ALTER TYPE logeventtype ADD VALUE IF NOT EXISTS 'TOPIC_VOTE'")
    op.execute("ALTER TYPE logeventtype ADD VALUE IF NOT EXISTS 'TOPIC_UNVOTE'")

    # re-activate the transaction for any future migrations
    if connection is not None:
        connection.execution_options(isolation_level="READ_COMMITTED")


def downgrade():
    # can't remove from enums, do nothing
    pass
