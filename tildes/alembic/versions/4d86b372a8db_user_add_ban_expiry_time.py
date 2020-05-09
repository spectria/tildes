"""User: add ban_expiry_time

Revision ID: 4d86b372a8db
Revises: 9148909b78e9
Create Date: 2020-05-09 20:05:30.503634

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "4d86b372a8db"
down_revision = "9148909b78e9"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "users",
        sa.Column("ban_expiry_time", sa.TIMESTAMP(timezone=True), nullable=True),
    )


def downgrade():
    op.drop_column("users", "ban_expiry_time")
