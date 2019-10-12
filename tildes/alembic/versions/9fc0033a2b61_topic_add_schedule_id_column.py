"""Topic: add schedule_id column

Revision ID: 9fc0033a2b61
Revises: 8326f8cc5ddd
Create Date: 2019-10-12 01:51:26.045258

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "9fc0033a2b61"
down_revision = "8326f8cc5ddd"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("topics", sa.Column("schedule_id", sa.Integer(), nullable=True))
    op.create_index(
        op.f("ix_topics_schedule_id"), "topics", ["schedule_id"], unique=False
    )
    op.create_foreign_key(
        op.f("fk_topics_schedule_id_topic_schedule"),
        "topics",
        "topic_schedule",
        ["schedule_id"],
        ["schedule_id"],
    )


def downgrade():
    op.drop_constraint(
        op.f("fk_topics_schedule_id_topic_schedule"), "topics", type_="foreignkey"
    )
    op.drop_index(op.f("ix_topics_schedule_id"), table_name="topics")
    op.drop_column("topics", "schedule_id")
