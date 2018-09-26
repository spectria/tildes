"""User: track last usage of exemplary label

Revision ID: 8e54f422541c
Revises: 5cd2db18b722
Create Date: 2018-09-26 00:22:02.728425

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "8e54f422541c"
down_revision = "5cd2db18b722"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "users",
        sa.Column(
            "last_exemplary_label_time", sa.TIMESTAMP(timezone=True), nullable=True
        ),
    )

    op.execute(
        """
        CREATE OR REPLACE FUNCTION update_user_last_exemplary_label_time() RETURNS TRIGGER AS $$
        BEGIN
            UPDATE users
                SET last_exemplary_label_time = NOW()
                WHERE user_id = NEW.user_id;

            RETURN NULL;
        END
        $$ LANGUAGE plpgsql;
    """
    )

    op.execute(
        """
        CREATE TRIGGER update_user_last_exemplary_label_time
            AFTER INSERT ON comment_labels
            FOR EACH ROW
            WHEN (NEW.label = 'EXEMPLARY')
            EXECUTE PROCEDURE update_user_last_exemplary_label_time();
    """
    )


def downgrade():
    op.execute("DROP TRIGGER update_user_last_exemplary_label_time ON comment_labels")
    op.execute("DROP FUNCTION update_user_last_exemplary_label_time()")

    op.drop_column("users", "last_exemplary_label_time")
