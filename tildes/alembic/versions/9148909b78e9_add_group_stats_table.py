"""Add group_stats table

Revision ID: 9148909b78e9
Revises: fe91222503ef
Create Date: 2020-03-06 02:27:31.720325

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "9148909b78e9"
down_revision = "fe91222503ef"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "group_stats",
        sa.Column("group_id", sa.Integer(), nullable=False),
        sa.Column(
            "stat",
            postgresql.ENUM("TOPICS_POSTED", "COMMENTS_POSTED", name="groupstattype"),
            nullable=False,
        ),
        sa.Column("period", postgresql.TSTZRANGE(), nullable=False),
        sa.Column("value", sa.Float(), nullable=False),
        sa.ForeignKeyConstraint(
            ["group_id"],
            ["groups.group_id"],
            name=op.f("fk_group_stats_group_id_groups"),
        ),
        sa.PrimaryKeyConstraint(
            "group_id", "stat", "period", name=op.f("pk_group_stats")
        ),
    )
    op.create_index(
        "ix_group_stats_period_gist",
        "group_stats",
        ["period"],
        unique=False,
        postgresql_using="gist",
    )


def downgrade():
    op.drop_index("ix_group_stats_period_gist", table_name="group_stats")
    op.drop_table("group_stats")
