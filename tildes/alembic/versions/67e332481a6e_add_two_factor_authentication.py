"""Add two-factor authentication

Revision ID: 67e332481a6e
Revises: fab922a8bb04
Create Date: 2018-07-31 02:53:50.182862

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "67e332481a6e"
down_revision = "fab922a8bb04"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "users",
        sa.Column(
            "two_factor_backup_codes", postgresql.ARRAY(sa.Text()), nullable=True
        ),
    )
    op.add_column(
        "users",
        sa.Column(
            "two_factor_enabled", sa.Boolean(), server_default="false", nullable=False
        ),
    )
    op.add_column("users", sa.Column("two_factor_secret", sa.Text(), nullable=True))


def downgrade():
    op.drop_column("users", "two_factor_secret")
    op.drop_column("users", "two_factor_enabled")
    op.drop_column("users", "two_factor_backup_codes")
