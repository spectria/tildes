"""Add user bio column

Revision ID: 3f83028d1673
Revises: 4ebc3ca32b48
Create Date: 2019-02-20 08:17:49.636855

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "3f83028d1673"
down_revision = "4ebc3ca32b48"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("users", sa.Column("bio_markdown", sa.Text(), nullable=True))
    op.add_column("users", sa.Column("bio_rendered_html", sa.Text(), nullable=True))
    op.create_check_constraint(
        "bio_markdown_length", "users", "LENGTH(bio_markdown) <= 2000"
    )


def downgrade():
    op.drop_constraint("ck_users_bio_markdown_length", "users")
    op.drop_column("users", "bio_rendered_html")
    op.drop_column("users", "bio_markdown")
