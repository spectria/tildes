"""Add comment excerpt

Revision ID: b9d9ae4c2286
Revises: b424479202f9
Create Date: 2018-08-28 02:42:48.436246

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.ext.declarative import declarative_base

from tildes.lib.string import extract_text_from_html, truncate_string


# revision identifiers, used by Alembic.
revision = "b9d9ae4c2286"
down_revision = "b424479202f9"
branch_labels = None
depends_on = None


Base = declarative_base()


# declare a minimal comments table here - we don't want the migration to be potentially
# impacted by future changes to the model, so we shouldn't import the real one
class Comment(Base):
    __tablename__ = "comments"

    comment_id = sa.Column(sa.Integer, primary_key=True)
    is_deleted = sa.Column(sa.Boolean)
    rendered_html = sa.Column(sa.Text)
    excerpt = sa.Column(sa.Text)


def upgrade():
    op.add_column(
        "comments", sa.Column("excerpt", sa.Text(), server_default="", nullable=False)
    )

    # generate excerpts for all existing (non-deleted) comments
    session = sa.orm.Session(bind=op.get_bind())
    comments = session.query(Comment).filter(Comment.is_deleted == False).all()
    for comment in comments:
        extracted_text = extract_text_from_html(comment.rendered_html)
        comment.excerpt = truncate_string(
            extracted_text, length=200, truncate_at_chars=" "
        )
    session.commit()


def downgrade():
    op.drop_column("comments", "excerpt")
