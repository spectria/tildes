"""Add topic_schedule table

Revision ID: 20b5f07e5f80
Revises: d56e71257a86
Create Date: 2019-10-02 22:08:13.324006

"""
from alembic import op
import sqlalchemy as sa

from tildes.lib.database import ArrayOfLtree


# revision identifiers, used by Alembic.
revision = "20b5f07e5f80"
down_revision = "d56e71257a86"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "topic_schedule",
        sa.Column("schedule_id", sa.Integer(), nullable=False),
        sa.Column("group_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column(
            "created_time",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("markdown", sa.Text(), nullable=False),
        sa.Column("tags", ArrayOfLtree(), server_default="{}", nullable=False),
        sa.Column("next_post_time", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("recurrence_rule", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(
            ["group_id"],
            ["groups.group_id"],
            name=op.f("fk_topic_schedule_group_id_groups"),
        ),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.user_id"], name=op.f("fk_topic_schedule_user_id_users")
        ),
        sa.PrimaryKeyConstraint("schedule_id", name=op.f("pk_topic_schedule")),
    )
    op.create_index(
        op.f("ix_topic_schedule_group_id"), "topic_schedule", ["group_id"], unique=False
    )
    op.create_index(
        op.f("ix_topic_schedule_next_post_time"),
        "topic_schedule",
        ["next_post_time"],
        unique=False,
    )
    op.create_check_constraint("title_length", "topic_schedule", "LENGTH(title) <= 200")

    # add the generic Tildes user (used to post scheduled topics by default)
    op.execute(
        """
        INSERT INTO users (user_id, username, password_hash)
        VALUES(-1, 'Tildes', '')
        ON CONFLICT DO NOTHING
    """
    )


def downgrade():
    op.drop_constraint("ck_topic_schedule_title_length", "topic_schedule")
    op.drop_index(op.f("ix_topic_schedule_next_post_time"), table_name="topic_schedule")
    op.drop_index(op.f("ix_topic_schedule_group_id"), table_name="topic_schedule")
    op.drop_table("topic_schedule")

    # don't delete the Tildes user, won't work if it posted any topics
