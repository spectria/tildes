"""Add comment sort order account setting

Revision ID: 51a1012f4f63
Revises: 9b7a7b906956
Create Date: 2020-02-07 22:38:08.826608

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "51a1012f4f63"
down_revision = "9b7a7b906956"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        "create type commenttreesortoption as enum('VOTES', 'NEWEST', 'POSTED', 'RELEVANCE')"
    )
    op.add_column(
        "users",
        sa.Column(
            "comment_sort_order_default",
            postgresql.ENUM(
                "VOTES", "NEWEST", "POSTED", "RELEVANCE", name="commenttreesortoption"
            ),
            nullable=True,
        ),
    )


def downgrade():
    op.drop_column("users", "comment_sort_order_default")
    op.execute("drop type commenttreesortoption")
