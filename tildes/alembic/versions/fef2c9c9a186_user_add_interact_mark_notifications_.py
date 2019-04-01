"""User: add interact_mark_notifications_read

Revision ID: fef2c9c9a186
Revises: beaa57144e49
Create Date: 2019-04-01 13:21:38.441021

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "fef2c9c9a186"
down_revision = "beaa57144e49"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "users",
        sa.Column(
            "interact_mark_notifications_read",
            sa.Boolean(),
            server_default="true",
            nullable=False,
        ),
    )


def downgrade():
    op.drop_column("users", "interact_mark_notifications_read")
