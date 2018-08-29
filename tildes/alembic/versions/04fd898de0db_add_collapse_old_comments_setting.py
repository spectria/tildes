"""Add collapse_old_comments setting

Revision ID: 04fd898de0db
Revises: b9d9ae4c2286
Create Date: 2018-08-29 03:07:10.278549

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "04fd898de0db"
down_revision = "b9d9ae4c2286"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "users",
        sa.Column(
            "collapse_old_comments", sa.Boolean(), server_default="true", nullable=False
        ),
    )


def downgrade():
    op.drop_column("users", "collapse_old_comments")
