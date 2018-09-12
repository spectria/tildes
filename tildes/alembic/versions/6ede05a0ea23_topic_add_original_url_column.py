"""Topic: add original_url column

Revision ID: 6ede05a0ea23
Revises: 09cfb27cc90e
Create Date: 2018-09-12 18:45:44.768561

"""
from alembic import op
import sqlalchemy as sa

from tildes.models.topic import Topic


# revision identifiers, used by Alembic.
revision = "6ede05a0ea23"
down_revision = "09cfb27cc90e"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("topics", sa.Column("original_url", sa.Text(), nullable=True))

    session = sa.orm.Session(bind=op.get_bind())
    session.query(Topic).update({"original_url": Topic.link}, synchronize_session=False)
    session.commit()


def downgrade():
    op.drop_column("topics", "original_url")
