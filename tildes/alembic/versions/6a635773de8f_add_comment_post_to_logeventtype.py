"""Add COMMENT_POST to logeventtype

Revision ID: 6a635773de8f
Revises: b3be50625592
Create Date: 2018-08-26 01:56:13.511360

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "6a635773de8f"
down_revision = "b3be50625592"
branch_labels = None
depends_on = None


def upgrade():
    # ALTER TYPE doesn't work from inside a transaction, disable it
    connection = None
    if not op.get_context().as_sql:
        connection = op.get_bind()
        connection.execution_options(isolation_level="AUTOCOMMIT")

    op.execute("ALTER TYPE logeventtype ADD VALUE IF NOT EXISTS 'COMMENT_POST'")

    # re-activate the transaction for any future migrations
    if connection is not None:
        connection.execution_options(isolation_level="READ_COMMITTED")


def downgrade():
    # can't remove from enums, do nothing
    pass
