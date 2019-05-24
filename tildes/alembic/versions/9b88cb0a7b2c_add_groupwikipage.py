"""Add GroupWikiPage

Revision ID: 9b88cb0a7b2c
Revises: 53f81a72f076
Create Date: 2019-05-24 18:47:29.828223

"""
from alembic import op
import sqlalchemy as sa

from tildes.lib.database import CIText

# revision identifiers, used by Alembic.
revision = "9b88cb0a7b2c"
down_revision = "53f81a72f076"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "group_wiki_pages",
        sa.Column("group_id", sa.Integer(), nullable=False),
        sa.Column("slug", CIText(), nullable=False),
        sa.Column("page_name", sa.Text(), nullable=False),
        sa.Column(
            "created_time",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
        sa.Column("last_edited_time", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("rendered_html", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(
            ["group_id"],
            ["groups.group_id"],
            name=op.f("fk_group_wiki_pages_group_id_groups"),
        ),
        sa.PrimaryKeyConstraint("group_id", "slug", name=op.f("pk_group_wiki_pages")),
    )
    op.create_index(
        op.f("ix_group_wiki_pages_last_edited_time"),
        "group_wiki_pages",
        ["last_edited_time"],
        unique=False,
    )
    op.create_check_constraint(
        "page_name_length", "group_wiki_pages", "LENGTH(page_name) <= 40"
    )


def downgrade():
    op.drop_constraint("ck_group_wiki_pages_page_name_length", "group_wiki_pages")
    op.drop_index(
        op.f("ix_group_wiki_pages_last_edited_time"), table_name="group_wiki_pages"
    )
    op.drop_table("group_wiki_pages")
