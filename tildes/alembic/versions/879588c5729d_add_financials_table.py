"""Add financials table

Revision ID: 879588c5729d
Revises: fa14e9f5ebe5
Create Date: 2019-11-05 19:50:13.973734

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "879588c5729d"
down_revision = "fa14e9f5ebe5"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "financials",
        sa.Column("entry_id", sa.Integer(), nullable=False),
        sa.Column(
            "entry_type",
            postgresql.ENUM("EXPENSE", "GOAL", "INCOME", name="financialentrytype"),
            nullable=False,
        ),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("amount", sa.Numeric(scale=2), nullable=False),
        sa.Column("date_range", postgresql.DATERANGE(), nullable=False),
        sa.Column(
            "is_approximate", sa.Boolean(), server_default="false", nullable=False
        ),
        sa.PrimaryKeyConstraint("entry_id", name=op.f("pk_financials")),
    )
    op.create_index(
        "ix_financials_date_range_gist",
        "financials",
        ["date_range"],
        unique=False,
        postgresql_using="gist",
    )


def downgrade():
    op.drop_index("ix_financials_date_range_gist", table_name="financials")
    op.drop_table("financials")

    op.execute("DROP TYPE financialentrytype")
