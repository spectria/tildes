"""Add user mention notifications from comments

Revision ID: f1ecbf24c212
Revises: de83b8750123
Create Date: 2018-07-19 02:32:43.684716

"""
from alembic import op


# revision identifiers, used by Alembic.
revision = "f1ecbf24c212"
down_revision = "de83b8750123"
branch_labels = None
depends_on = None


def upgrade():
    # ALTER TYPE doesn't work from inside a transaction, disable it
    connection = None
    if not op.get_context().as_sql:
        connection = op.get_bind()
        connection.execution_options(isolation_level="AUTOCOMMIT")

    op.execute(
        "ALTER TYPE commentnotificationtype ADD VALUE IF NOT EXISTS 'USER_MENTION'"
    )

    # re-activate the transaction for any future migrations
    if connection is not None:
        connection.execution_options(isolation_level="READ_COMMITTED")

    op.execute(
        """
    CREATE OR REPLACE FUNCTION send_rabbitmq_message_for_comment() RETURNS TRIGGER AS $$
    DECLARE
        affected_row RECORD;
        payload TEXT;
    BEGIN
        IF (TG_OP = 'INSERT' OR TG_OP = 'UPDATE') THEN
            affected_row := NEW;
        ELSIF (TG_OP = 'DELETE') THEN
            affected_row := OLD;
        END IF;

        payload := json_build_object('comment_id', affected_row.comment_id, 'event_type', TG_OP);

        PERFORM send_rabbitmq_message('comment.' || TG_ARGV[0], payload);

        RETURN NULL;
    END;
    $$ LANGUAGE plpgsql;
    """
    )
    op.execute(
        """
        CREATE TRIGGER send_rabbitmq_message_for_comment_insert
            AFTER INSERT ON comments
            FOR EACH ROW
            EXECUTE PROCEDURE send_rabbitmq_message_for_comment('created');
    """
    )
    op.execute(
        """
        CREATE TRIGGER send_rabbitmq_message_for_comment_edit
            AFTER UPDATE ON comments
            FOR EACH ROW
            WHEN (OLD.markdown IS DISTINCT FROM NEW.markdown)
            EXECUTE PROCEDURE send_rabbitmq_message_for_comment('edited');
    """
    )


def downgrade():
    op.execute("DROP TRIGGER send_rabbitmq_message_for_comment_insert ON comments")
    op.execute("DROP TRIGGER send_rabbitmq_message_for_comment_edit ON comments")
    op.execute("DROP FUNCTION send_rabbitmq_message_for_comment")
