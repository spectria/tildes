"""Add COMMENT_REMOVE and COMMENT_UNREMOVE to logeventtype

Revision ID: 3fbddcba0e3b
Revises: 6a635773de8f
Create Date: 2018-08-26 04:34:51.741972

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "3fbddcba0e3b"
down_revision = "6a635773de8f"
branch_labels = None
depends_on = None


def upgrade():
    # ALTER TYPE doesn't work from inside a transaction, disable it
    connection = None
    if not op.get_context().as_sql:
        connection = op.get_bind()
        connection.execution_options(isolation_level="AUTOCOMMIT")

    op.execute("ALTER TYPE logeventtype ADD VALUE IF NOT EXISTS 'COMMENT_REMOVE'")
    op.execute("ALTER TYPE logeventtype ADD VALUE IF NOT EXISTS 'COMMENT_UNREMOVE'")

    # re-activate the transaction for any future migrations
    if connection is not None:
        connection.execution_options(isolation_level="READ_COMMITTED")


def downgrade():
    # no way to remove enum values, just do nothing
    pass
