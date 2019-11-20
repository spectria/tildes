"""Add is_voting_closed to comments and topics

Revision ID: 4d352e61a468
Revises: 879588c5729d
Create Date: 2019-11-15 23:58:09.613684

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "4d352e61a468"
down_revision = "879588c5729d"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "comments",
        sa.Column(
            "is_voting_closed", sa.Boolean(), server_default="false", nullable=False
        ),
    )
    op.create_index(
        op.f("ix_comments_is_voting_closed"),
        "comments",
        ["is_voting_closed"],
        unique=False,
    )
    op.add_column(
        "topics",
        sa.Column(
            "is_voting_closed", sa.Boolean(), server_default="false", nullable=False
        ),
    )
    op.create_index(
        op.f("ix_topics_is_voting_closed"), "topics", ["is_voting_closed"], unique=False
    )

    op.execute(
        """
        CREATE OR REPLACE FUNCTION update_comment_num_votes() RETURNS TRIGGER AS $$
        BEGIN
            IF (TG_OP = 'INSERT') THEN
                UPDATE comments
                    SET num_votes = num_votes + 1
                    WHERE comment_id = NEW.comment_id;
            ELSIF (TG_OP = 'DELETE') THEN
                UPDATE comments
                    SET num_votes = num_votes - 1
                    WHERE comment_id = OLD.comment_id
                        AND is_voting_closed = FALSE;
            END IF;

            RETURN NULL;
        END
        $$ LANGUAGE plpgsql;
        """
    )

    op.execute(
        """
        CREATE OR REPLACE FUNCTION update_topic_num_votes() RETURNS TRIGGER AS $$
        BEGIN
            IF (TG_OP = 'INSERT') THEN
                UPDATE topics
                    SET num_votes = num_votes + 1
                    WHERE topic_id = NEW.topic_id;
            ELSIF (TG_OP = 'DELETE') THEN
                UPDATE topics
                    SET num_votes = num_votes - 1
                    WHERE topic_id = OLD.topic_id
                        AND is_voting_closed = FALSE;
            END IF;

            RETURN NULL;
        END
        $$ LANGUAGE plpgsql;
        """
    )


def downgrade():
    op.drop_index(op.f("ix_topics_is_voting_closed"), table_name="topics")
    op.drop_column("topics", "is_voting_closed")
    op.drop_index(op.f("ix_comments_is_voting_closed"), table_name="comments")
    op.drop_column("comments", "is_voting_closed")

    op.execute(
        """
        CREATE OR REPLACE FUNCTION update_comment_num_votes() RETURNS TRIGGER AS $$
        BEGIN
            IF (TG_OP = 'INSERT') THEN
                UPDATE comments
                    SET num_votes = num_votes + 1
                    WHERE comment_id = NEW.comment_id;
            ELSIF (TG_OP = 'DELETE') THEN
                UPDATE comments
                    SET num_votes = num_votes - 1
                    WHERE comment_id = OLD.comment_id;
            END IF;

            RETURN NULL;
        END
        $$ LANGUAGE plpgsql;
        """
    )

    op.execute(
        """
        CREATE OR REPLACE FUNCTION update_topic_num_votes() RETURNS TRIGGER AS $$
        BEGIN
            IF (TG_OP = 'INSERT') THEN
                UPDATE topics
                    SET num_votes = num_votes + 1
                    WHERE topic_id = NEW.topic_id;
            ELSIF (TG_OP = 'DELETE') THEN
                UPDATE topics
                    SET num_votes = num_votes - 1
                    WHERE topic_id = OLD.topic_id;
            END IF;

            RETURN NULL;
        END
        $$ LANGUAGE plpgsql;
        """
    )
