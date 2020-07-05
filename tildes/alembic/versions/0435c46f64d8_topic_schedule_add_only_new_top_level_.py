"""topic_schedule: add only_new_top_level_comments_in_latest

Revision ID: 0435c46f64d8
Revises: 468cf81f4a6b
Create Date: 2020-07-05 19:33:17.746617

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "0435c46f64d8"
down_revision = "468cf81f4a6b"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "topic_schedule",
        sa.Column(
            "only_new_top_level_comments_in_latest",
            sa.Boolean(),
            server_default="true",
            nullable=False,
        ),
    )


def downgrade():
    op.drop_column("topic_schedule", "only_new_top_level_comments_in_latest")
