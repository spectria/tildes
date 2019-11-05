"""Add user_rate_limit table

Revision ID: fa14e9f5ebe5
Revises: b761d0185ca0
Create Date: 2019-11-05 18:11:34.303355

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "fa14e9f5ebe5"
down_revision = "b761d0185ca0"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "user_rate_limit",
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("action", sa.Text(), nullable=False),
        sa.Column("period", sa.Interval(), nullable=False),
        sa.Column("limit", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.user_id"],
            name=op.f("fk_user_rate_limit_user_id_users"),
        ),
        sa.PrimaryKeyConstraint("user_id", "action", name=op.f("pk_user_rate_limit")),
    )


def downgrade():
    op.drop_table("user_rate_limit")
