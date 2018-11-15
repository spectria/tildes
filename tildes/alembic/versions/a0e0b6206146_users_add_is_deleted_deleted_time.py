"""Users: Add is_deleted/deleted_time

Revision ID: a0e0b6206146
Revises: 53567981cdf4
Create Date: 2018-11-13 23:49:20.764289

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "a0e0b6206146"
down_revision = "53567981cdf4"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "users", sa.Column("deleted_time", sa.TIMESTAMP(timezone=True), nullable=True)
    )
    op.add_column(
        "users",
        sa.Column("is_deleted", sa.Boolean(), server_default="false", nullable=False),
    )
    op.create_index(op.f("ix_users_is_deleted"), "users", ["is_deleted"], unique=False)

    op.execute(
        """
        CREATE OR REPLACE FUNCTION set_user_deleted_time() RETURNS TRIGGER AS $$
        BEGIN
            NEW.deleted_time := current_timestamp;

            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;

        CREATE TRIGGER delete_user_set_deleted_time_update
            BEFORE UPDATE ON users
            FOR EACH ROW
            WHEN (OLD.is_deleted = false AND NEW.is_deleted = true)
            EXECUTE PROCEDURE set_user_deleted_time();
    """
    )


def downgrade():
    op.execute("DROP TRIGGER delete_user_set_deleted_time_update ON users")
    op.execute("DROP FUNCTION set_user_deleted_time")

    op.drop_index(op.f("ix_users_is_deleted"), table_name="users")
    op.drop_column("users", "is_deleted")
    op.drop_column("users", "deleted_time")
