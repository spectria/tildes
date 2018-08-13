"""Add setting to open text links in new tab

Revision ID: de83b8750123
Revises: 2512581c91b3
Create Date: 2018-07-24 03:10:59.485645

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "de83b8750123"
down_revision = "2512581c91b3"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "users",
        sa.Column(
            "open_new_tab_text", sa.Boolean(), server_default="false", nullable=False
        ),
    )


def downgrade():
    op.drop_column("users", "open_new_tab_text")
