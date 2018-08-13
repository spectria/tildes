"""Add setting to open links in new tab

Revision ID: 2512581c91b3
Revises:
Create Date: 2018-07-21 22:23:49.563318

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "2512581c91b3"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "users",
        sa.Column(
            "open_new_tab_external",
            sa.Boolean(),
            server_default="false",
            nullable=False,
        ),
    )
    op.add_column(
        "users",
        sa.Column(
            "open_new_tab_internal",
            sa.Boolean(),
            server_default="false",
            nullable=False,
        ),
    )


def downgrade():
    op.drop_column("users", "open_new_tab_internal")
    op.drop_column("users", "open_new_tab_external")
