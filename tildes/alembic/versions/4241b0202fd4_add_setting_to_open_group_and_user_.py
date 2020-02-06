"""Add setting to open group and user links in new tab

Revision ID: 4241b0202fd4
Revises: 34753d8124b4
Create Date: 2020-02-06 16:59:10.720154

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "4241b0202fd4"
down_revision = "34753d8124b4"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "users",
        sa.Column(
            "open_new_tab_group", sa.Boolean(), server_default="false", nullable=False
        ),
    )
    op.add_column(
        "users",
        sa.Column(
            "open_new_tab_user", sa.Boolean(), server_default="false", nullable=False
        ),
    )


def downgrade():
    op.drop_column("users", "open_new_tab_user")
    op.drop_column("users", "open_new_tab_group")
