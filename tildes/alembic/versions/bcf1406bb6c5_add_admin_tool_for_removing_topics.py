"""Add admin tool for removing topics

Revision ID: bcf1406bb6c5
Revises: 50c251c4a19c
Create Date: 2018-08-22 23:56:41.733065

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "bcf1406bb6c5"
down_revision = "50c251c4a19c"
branch_labels = None
depends_on = None


def upgrade():
    # ALTER TYPE doesn't work from inside a transaction, disable it
    connection = None
    if not op.get_context().as_sql:
        connection = op.get_bind()
        connection.execution_options(isolation_level="AUTOCOMMIT")

    op.execute("ALTER TYPE logeventtype ADD VALUE IF NOT EXISTS 'TOPIC_REMOVE'")
    op.execute("ALTER TYPE logeventtype ADD VALUE IF NOT EXISTS 'TOPIC_UNREMOVE'")

    # re-activate the transaction for any future migrations
    if connection is not None:
        connection.execution_options(isolation_level="READ_COMMITTED")


def downgrade():
    # no way to remove enum values, just do nothing
    pass
