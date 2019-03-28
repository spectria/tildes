"""comment_labels: Send rabbitmq message on insert

Revision ID: beaa57144e49
Revises: 380a76d4a722
Create Date: 2019-03-28 18:37:58.995944

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "beaa57144e49"
down_revision = "380a76d4a722"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        """
        CREATE OR REPLACE FUNCTION send_rabbitmq_message_for_comment_label() RETURNS TRIGGER AS $$
        DECLARE
            affected_row RECORD;
            payload TEXT;
        BEGIN
            IF (TG_OP = 'INSERT' OR TG_OP = 'UPDATE') THEN
                affected_row := NEW;
            ELSIF (TG_OP = 'DELETE') THEN
                affected_row := OLD;
            END IF;

            payload := json_build_object(
                'comment_id', affected_row.comment_id,
                'label', affected_row.label,
                'user_id', affected_row.user_id);

            PERFORM send_rabbitmq_message('comment_label.' || TG_ARGV[0], payload);

            RETURN NULL;
        END;
        $$ LANGUAGE plpgsql;
    """
    )

    op.execute(
        """
        CREATE TRIGGER send_rabbitmq_message_for_comment_label_insert
            AFTER INSERT ON comment_labels
            FOR EACH ROW
            EXECUTE PROCEDURE send_rabbitmq_message_for_comment_label('created');
    """
    )


def downgrade():
    op.execute(
        "DROP TRIGGER send_rabbitmq_message_for_comment_label_insert ON comment_labels"
    )
    op.execute("DROP FUNCTION send_rabbitmq_message_for_comment_label")
