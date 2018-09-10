"""Add scraper_results table

Revision ID: 09cfb27cc90e
Revises: 04fd898de0db
Create Date: 2018-09-09 21:22:32.769786

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "09cfb27cc90e"
down_revision = "04fd898de0db"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "scraper_results",
        sa.Column("result_id", sa.Integer(), nullable=False),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column(
            "scraper_type",
            postgresql.ENUM("EMBEDLY", name="scrapertype"),
            nullable=False,
        ),
        sa.Column(
            "scrape_time",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
        sa.Column("data", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.PrimaryKeyConstraint("result_id", name=op.f("pk_scraper_results")),
    )
    op.create_index(
        op.f("ix_scraper_results_scrape_time"),
        "scraper_results",
        ["scrape_time"],
        unique=False,
    )
    op.create_index(
        op.f("ix_scraper_results_url"), "scraper_results", ["url"], unique=False
    )


def downgrade():
    op.drop_index(op.f("ix_scraper_results_url"), table_name="scraper_results")
    op.drop_index(op.f("ix_scraper_results_scrape_time"), table_name="scraper_results")
    op.drop_table("scraper_results")
