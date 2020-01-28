"""Drop track_comment_visits column on users

Revision ID: 6c840340ab86
Revises: cc12ea6c616d
Create Date: 2020-01-27 21:42:25.565355

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "6c840340ab86"
down_revision = "cc12ea6c616d"
branch_labels = None
depends_on = None


def upgrade():
    op.drop_column("users", "track_comment_visits")


def downgrade():
    op.add_column(
        "users",
        sa.Column(
            "track_comment_visits",
            sa.BOOLEAN(),
            server_default=sa.text("false"),
            nullable=False,
        ),
    )
