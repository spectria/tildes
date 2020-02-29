"""Rename column for restricted-posting groups

Revision ID: 84dc19f6e876
Revises: 054aaef690cd
Create Date: 2020-02-29 03:03:31.968814

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "84dc19f6e876"
down_revision = "054aaef690cd"
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column(
        "groups",
        "is_admin_posting_only",
        new_column_name="requires_permission_to_post_topics",
    )

    op.execute(
        "update user_permissions set permission = 'wiki.edit' where permission = 'wiki'"
    )


def downgrade():
    op.alter_column(
        "groups",
        "requires_permission_to_post_topics",
        new_column_name="is_admin_posting_only",
    )

    op.execute(
        "update user_permissions set permission = 'wiki' where permission = 'wiki.edit'"
    )
