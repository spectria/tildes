"""Add tag-related user settings

Revision ID: d56e71257a86
Revises: a195ddbb4be6
Create Date: 2019-09-27 23:53:34.287619

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "d56e71257a86"
down_revision = "a195ddbb4be6"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "users",
        sa.Column(
            "show_tags_in_listings",
            sa.Boolean(),
            server_default="false",
            nullable=False,
        ),
    )
    op.add_column(
        "users",
        sa.Column(
            "show_tags_on_new_topic",
            sa.Boolean(),
            server_default="false",
            nullable=False,
        ),
    )

    # enable the new settings for any users that have the "topic.tag" permission
    op.execute(
        """
        UPDATE users
        SET show_tags_in_listings = true, show_tags_on_new_topic = true
        WHERE permissions ? 'topic.tag'
    """
    )

    # show tagging on new topics for any users that have changed tags recently or posted
    # a topic that has tags and wasn't re-tagged by another user
    op.execute(
        """
        UPDATE users
        SET show_tags_on_new_topic = true
        WHERE user_id IN (
            SELECT DISTINCT(user_id) FROM log_topics WHERE event_type = 'TOPIC_TAG'
        ) OR user_id IN (
            SELECT DISTINCT(user_id) FROM topics
            WHERE tags != '{}' AND created_time > NOW() - INTERVAL '30 days'
            AND NOT EXISTS (
                SELECT * FROM log_topics
                WHERE topic_id = topics.topic_id
                AND event_type = 'TOPIC_TAG'
                AND user_id != topics.user_id
            )
        )
    """
    )


def downgrade():
    op.drop_column("users", "show_tags_on_new_topic")
    op.drop_column("users", "show_tags_in_listings")
