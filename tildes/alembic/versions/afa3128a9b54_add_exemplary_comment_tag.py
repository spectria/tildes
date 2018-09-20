"""Add Exemplary comment tag

Revision ID: afa3128a9b54
Revises: 1ade2bf86efc
Create Date: 2018-09-18 22:17:39.619439

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "afa3128a9b54"
down_revision = "1ade2bf86efc"
branch_labels = None
depends_on = None


def upgrade():
    # ALTER TYPE doesn't work from inside a transaction, disable it
    connection = None
    if not op.get_context().as_sql:
        connection = op.get_bind()
        connection.execution_options(isolation_level="AUTOCOMMIT")

    op.execute("ALTER TYPE commenttagoption ADD VALUE IF NOT EXISTS 'EXEMPLARY'")

    # re-activate the transaction for any future migrations
    if connection is not None:
        connection.execution_options(isolation_level="READ_COMMITTED")


def downgrade():
    pass
