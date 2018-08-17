"""Add topic and comment bookmark tables

Revision ID: 53567981cdf4
Revises: 5a7dc1032efc
Create Date: 2018-08-17 17:57:22.171858

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "53567981cdf4"
down_revision = "5a7dc1032efc"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "topic_bookmarks",
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("topic_id", sa.Integer(), nullable=False),
        sa.Column(
            "created_time",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["topic_id"],
            ["topics.topic_id"],
            name=op.f("fk_topic_bookmarks_topic_id_topics"),
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.user_id"],
            name=op.f("fk_topic_bookmarks_user_id_users"),
        ),
        sa.PrimaryKeyConstraint("user_id", "topic_id", name=op.f("pk_topic_bookmarks")),
    )
    op.create_index(
        op.f("ix_topic_bookmarks_created_time"),
        "topic_bookmarks",
        ["created_time"],
        unique=False,
    )

    op.create_table(
        "comment_bookmarks",
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("comment_id", sa.Integer(), nullable=False),
        sa.Column(
            "created_time",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["comment_id"],
            ["comments.comment_id"],
            name=op.f("fk_comment_bookmarks_comment_id_comments"),
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.user_id"],
            name=op.f("fk_comment_bookmarks_user_id_users"),
        ),
        sa.PrimaryKeyConstraint(
            "user_id", "comment_id", name=op.f("pk_comment_bookmarks")
        ),
    )
    op.create_index(
        op.f("ix_comment_bookmarks_created_time"),
        "comment_bookmarks",
        ["created_time"],
        unique=False,
    )


def downgrade():
    op.drop_index(
        op.f("ix_comment_bookmarks_created_time"), table_name="comment_bookmarks"
    )
    op.drop_table("comment_bookmarks")
    op.drop_index(op.f("ix_topic_bookmarks_created_time"), table_name="topic_bookmarks")
    op.drop_table("topic_bookmarks")
