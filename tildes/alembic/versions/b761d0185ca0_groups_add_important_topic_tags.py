"""Groups: add important_topic_tags

Revision ID: b761d0185ca0
Revises: 679090fd4977
Create Date: 2019-10-26 01:51:21.231463

"""
from alembic import op
import sqlalchemy as sa

from tildes.lib.database import TagList


# revision identifiers, used by Alembic.
revision = "b761d0185ca0"
down_revision = "679090fd4977"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "groups",
        sa.Column(
            "important_topic_tags", TagList(), server_default="{}", nullable=False
        ),
    )


def downgrade():
    op.drop_column("groups", "important_topic_tags")
