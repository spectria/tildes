"""Add group_scripts table

Revision ID: 55f4c1f951d5
Revises: 28d7ce2c4825
Create Date: 2020-11-30 19:54:30.731335

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "55f4c1f951d5"
down_revision = "28d7ce2c4825"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "group_scripts",
        sa.Column("script_id", sa.Integer(), nullable=False),
        sa.Column("group_id", sa.Integer(), nullable=True),
        sa.Column("code", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(
            ["group_id"],
            ["groups.group_id"],
            name=op.f("fk_group_scripts_group_id_groups"),
        ),
        sa.PrimaryKeyConstraint("script_id", name=op.f("pk_group_scripts")),
    )


def downgrade():
    op.drop_table("group_scripts")
