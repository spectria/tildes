"""User: add banned_time

Revision ID: 380a76d4a722
Revises: 3f83028d1673
Create Date: 2019-03-28 04:04:49.089292

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "380a76d4a722"
down_revision = "3f83028d1673"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "users", sa.Column("banned_time", sa.TIMESTAMP(timezone=True), nullable=True)
    )
    op.execute(
        """
        CREATE OR REPLACE FUNCTION set_user_banned_time() RETURNS TRIGGER AS $$
        BEGIN
            NEW.banned_time := current_timestamp;

            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """
    )
    op.execute(
        """
        CREATE TRIGGER ban_user_set_banned_time_update
            BEFORE UPDATE ON users
            FOR EACH ROW
            WHEN (OLD.is_banned = false AND NEW.is_banned = true)
            EXECUTE PROCEDURE set_user_banned_time();
    """
    )


def downgrade():
    op.execute("DROP TRIGGER ban_user_set_banned_time_update ON users")
    op.execute("DROP FUNCTION set_user_banned_time")
    op.drop_column("users", "banned_time")
