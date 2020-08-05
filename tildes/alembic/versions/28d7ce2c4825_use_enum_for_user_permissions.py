"""Use enum for user permissions

Revision ID: 28d7ce2c4825
Revises: 82e9801eb2d6
Create Date: 2020-08-05 20:32:51.047215

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "28d7ce2c4825"
down_revision = "82e9801eb2d6"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        """
        create type userpermission as enum(
            'comment.remove',
            'comment.view_labels',
            'topic.edit_by_generic_user',
            'topic.edit_link',
            'topic.edit_title',
            'topic.lock',
            'topic.move',
            'topic.post',
            'topic.remove',
            'topic.tag',
            'user.ban',
            'user.view_removed_posts',
            'wiki.edit'
        )
        """
    )
    op.execute(
        """
        alter table user_permissions
        alter column permission type userpermission using permission::userpermission
        """
    )


def downgrade():
    op.execute("alter table user_permissions alter column permission type text")
    op.execute("drop type userpermission")
