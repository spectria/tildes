"""Group: add common_topic_tags

Revision ID: 53f81a72f076
Revises: fef2c9c9a186
Create Date: 2019-04-24 17:50:24.360780

"""
from alembic import op
import sqlalchemy as sa

from tildes.lib.database import ArrayOfLtree


# revision identifiers, used by Alembic.
revision = "53f81a72f076"
down_revision = "fef2c9c9a186"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "groups",
        sa.Column(
            "common_topic_tags", ArrayOfLtree(), server_default="{}", nullable=False
        ),
    )


def downgrade():
    op.drop_column("groups", "common_topic_tags")
