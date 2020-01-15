"""Extend topic indexes for keyset pagination

Revision ID: f4e1ef359307
Revises: 4e101aae77cd
Create Date: 2020-01-15 20:52:23.380355

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "f4e1ef359307"
down_revision = "4e101aae77cd"
branch_labels = None
depends_on = None


def upgrade():
    op.create_index(
        "ix_topics_created_time_keyset",
        "topics",
        [sa.text("created_time DESC"), sa.text("topic_id DESC")],
        unique=False,
    )
    op.create_index(
        "ix_topics_last_activity_time_keyset",
        "topics",
        [sa.text("last_activity_time DESC"), sa.text("topic_id DESC")],
        unique=False,
    )
    op.create_index(
        "ix_topics_last_interesting_activity_time_keyset",
        "topics",
        [sa.text("last_interesting_activity_time DESC"), sa.text("topic_id DESC")],
        unique=False,
    )
    op.create_index(
        "ix_topics_num_comments_keyset",
        "topics",
        [sa.text("num_comments DESC"), sa.text("topic_id DESC")],
        unique=False,
    )
    op.create_index(
        "ix_topics_num_votes_keyset",
        "topics",
        [sa.text("num_votes DESC"), sa.text("topic_id DESC")],
        unique=False,
    )
    op.drop_index("ix_topics_created_time", table_name="topics")
    op.drop_index("ix_topics_last_activity_time", table_name="topics")
    op.drop_index("ix_topics_last_interesting_activity_time", table_name="topics")
    op.drop_index("ix_topics_num_comments", table_name="topics")
    op.drop_index("ix_topics_num_votes", table_name="topics")


def downgrade():
    op.create_index("ix_topics_num_votes", "topics", ["num_votes"], unique=False)
    op.create_index("ix_topics_num_comments", "topics", ["num_comments"], unique=False)
    op.create_index(
        "ix_topics_last_interesting_activity_time",
        "topics",
        ["last_interesting_activity_time"],
        unique=False,
    )
    op.create_index(
        "ix_topics_last_activity_time", "topics", ["last_activity_time"], unique=False
    )
    op.create_index("ix_topics_created_time", "topics", ["created_time"], unique=False)
    op.drop_index("ix_topics_num_votes_keyset", table_name="topics")
    op.drop_index("ix_topics_num_comments_keyset", table_name="topics")
    op.drop_index(
        "ix_topics_last_interesting_activity_time_keyset", table_name="topics"
    )
    op.drop_index("ix_topics_last_activity_time_keyset", table_name="topics")
    op.drop_index("ix_topics_created_time_keyset", table_name="topics")
