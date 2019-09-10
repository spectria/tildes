"""Add solarized- prefix to default themes

Revision ID: a195ddbb4be6
Revises: f20ce28b1d5c
Create Date: 2019-09-10 04:13:50.950487

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "a195ddbb4be6"
down_revision = "f20ce28b1d5c"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        "UPDATE users SET theme_default = 'solarized-dark' WHERE theme_default = 'dark'"
    )
    op.execute(
        "UPDATE users SET theme_default = 'solarized-light' WHERE theme_default = 'light'"
    )


def downgrade():
    op.execute(
        "UPDATE users SET theme_default = 'dark' WHERE theme_default = 'solarized-dark'"
    )
    op.execute(
        "UPDATE users SET theme_default = 'light' WHERE theme_default = 'solarized-light'"
    )
