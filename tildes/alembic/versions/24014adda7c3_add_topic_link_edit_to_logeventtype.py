"""Add TOPIC_LINK_EDIT to logeventtype

Revision ID: 24014adda7c3
Revises: 7ac1aad64144
Create Date: 2019-03-14 21:57:27.057187

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "24014adda7c3"
down_revision = "7ac1aad64144"
branch_labels = None
depends_on = None


def upgrade():
    # ALTER TYPE doesn't work from inside a transaction, disable it
    connection = None
    if not op.get_context().as_sql:
        connection = op.get_bind()
        connection.execution_options(isolation_level="AUTOCOMMIT")

    op.execute("ALTER TYPE logeventtype ADD VALUE IF NOT EXISTS 'TOPIC_LINK_EDIT'")

    # re-activate the transaction for any future migrations
    if connection is not None:
        connection.execution_options(isolation_level="READ_COMMITTED")


def downgrade():
    # can't remove from enums, do nothing
    pass
