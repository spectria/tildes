"""Update post_topic permission to topic.post

Revision ID: 82e9801eb2d6
Revises: 0435c46f64d8
Create Date: 2020-08-05 00:05:46.690188

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "82e9801eb2d6"
down_revision = "0435c46f64d8"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        "update user_permissions set permission = 'topic.post' where permission = 'post_topic'"
    )


def downgrade():
    op.execute(
        "update user_permissions set permission = 'post_topic' where permission = 'topic.post'"
    )
