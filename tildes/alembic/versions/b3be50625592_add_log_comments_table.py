"""Add log_comments table

Revision ID: b3be50625592
Revises: a1708d376252
Create Date: 2018-08-23 04:20:55.819209

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "b3be50625592"
down_revision = "a1708d376252"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("CREATE TABLE log_comments (comment_id integer not null) INHERITS (log)")
    op.create_foreign_key(
        op.f("fk_log_comments_comment_id_comments"),
        "log_comments",
        "comments",
        ["comment_id"],
        ["comment_id"],
    )
    op.create_index(
        op.f("ix_log_comments_comment_id"), "log_comments", ["comment_id"], unique=False
    )

    # duplicate all the indexes/constraints from the base log table
    op.create_primary_key(op.f("pk_log_comments"), "log_comments", ["log_id"])
    op.create_index(
        op.f("ix_log_comments_event_time"), "log_comments", ["event_time"], unique=False
    )
    op.create_index(
        op.f("ix_log_comments_event_type"), "log_comments", ["event_type"], unique=False
    )
    op.create_index(
        op.f("ix_log_comments_ip_address"), "log_comments", ["ip_address"], unique=False
    )
    op.create_index(
        op.f("ix_log_comments_user_id"), "log_comments", ["user_id"], unique=False
    )

    op.create_foreign_key(
        op.f("fk_log_comments_user_id_users"),
        "log_comments",
        "users",
        ["user_id"],
        ["user_id"],
    )


def downgrade():
    op.drop_index(op.f("ix_log_comments_comment_id"), table_name="log_comments")
    op.drop_table("log_comments")
