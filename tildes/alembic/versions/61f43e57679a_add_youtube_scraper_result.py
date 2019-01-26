"""Add youtube scraper result

Revision ID: 61f43e57679a
Revises: a0e0b6206146
Create Date: 2019-01-26 20:02:27.642583

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "61f43e57679a"
down_revision = "a0e0b6206146"
branch_labels = None
depends_on = None


def upgrade():
    # ALTER TYPE doesn't work from inside a transaction, disable it
    connection = None
    if not op.get_context().as_sql:
        connection = op.get_bind()
        connection.execution_options(isolation_level="AUTOCOMMIT")

    op.execute("ALTER TYPE scrapertype ADD VALUE IF NOT EXISTS 'YOUTUBE'")

    # re-activate the transaction for any future migrations
    if connection is not None:
        connection.execution_options(isolation_level="READ_COMMITTED")


def downgrade():
    # can't remove from enums, do nothing
    pass
