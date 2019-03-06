"""Add topic_ignores

Revision ID: 4e101aae77cd
Revises: 4d352e61a468
Create Date: 2020-01-07 23:07:51.707034

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "4e101aae77cd"
down_revision = "4d352e61a468"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "topic_ignores",
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
            name=op.f("fk_topic_ignores_topic_id_topics"),
        ),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.user_id"], name=op.f("fk_topic_ignores_user_id_users")
        ),
        sa.PrimaryKeyConstraint("user_id", "topic_id", name=op.f("pk_topic_ignores")),
    )
    op.create_index(
        op.f("ix_topic_ignores_created_time"),
        "topic_ignores",
        ["created_time"],
        unique=False,
    )


def downgrade():
    op.drop_index(op.f("ix_topic_ignores_created_time"), table_name="topic_ignores")
    op.drop_table("topic_ignores")
