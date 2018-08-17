"""Switch to general permissions column

Revision ID: d33fb803a153
Revises: 67e332481a6e
Create Date: 2018-08-16 23:07:07.643208

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "d33fb803a153"
down_revision = "67e332481a6e"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "users",
        sa.Column(
            "permissions", postgresql.JSONB(astext_type=sa.Text()), nullable=True
        ),
    )
    op.drop_column("users", "is_admin")


def downgrade():
    op.add_column(
        "users",
        sa.Column(
            "is_admin",
            sa.BOOLEAN(),
            server_default=sa.text("false"),
            autoincrement=False,
            nullable=False,
        ),
    )
    op.drop_column("users", "permissions")
