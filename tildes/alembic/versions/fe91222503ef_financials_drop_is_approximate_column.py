"""Financials: Drop is_approximate column

Revision ID: fe91222503ef
Revises: 84dc19f6e876
Create Date: 2020-03-04 22:38:15.528403

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "fe91222503ef"
down_revision = "84dc19f6e876"
branch_labels = None
depends_on = None


def upgrade():
    op.drop_column("financials", "is_approximate")


def downgrade():
    op.add_column(
        "financials",
        sa.Column(
            "is_approximate",
            sa.BOOLEAN(),
            server_default=sa.text("false"),
            autoincrement=False,
            nullable=False,
        ),
    )
