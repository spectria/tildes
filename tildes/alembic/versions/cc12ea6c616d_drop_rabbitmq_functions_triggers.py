"""Drop rabbitmq functions/triggers

Revision ID: cc12ea6c616d
Revises: 4fb2c786c7a0
Create Date: 2020-01-19 21:29:41.337253

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "cc12ea6c616d"
down_revision = "4fb2c786c7a0"
branch_labels = None
depends_on = None


def upgrade():
    # scraper_results
    op.execute(
        "drop trigger send_rabbitmq_message_for_scraper_result_insert on scraper_results"
    )
    op.execute("drop function send_rabbitmq_message_for_scraper_result")

    # comment_labels
    op.execute(
        "drop trigger send_rabbitmq_message_for_comment_label_delete on comment_labels"
    )
    op.execute(
        "drop trigger send_rabbitmq_message_for_comment_label_insert on comment_labels"
    )
    op.execute("drop function send_rabbitmq_message_for_comment_label")

    # topics
    op.execute("drop trigger send_rabbitmq_message_for_topic_link_edit on topics")
    op.execute("drop trigger send_rabbitmq_message_for_topic_edit on topics")
    op.execute("drop trigger send_rabbitmq_message_for_topic_insert on topics")
    op.execute("drop function send_rabbitmq_message_for_topic")

    # comments
    op.execute("drop trigger send_rabbitmq_message_for_comment_unremove on comments")
    op.execute("drop trigger send_rabbitmq_message_for_comment_remove on comments")
    op.execute("drop trigger send_rabbitmq_message_for_comment_undelete on comments")
    op.execute("drop trigger send_rabbitmq_message_for_comment_delete on comments")
    op.execute("drop trigger send_rabbitmq_message_for_comment_edit on comments")
    op.execute("drop trigger send_rabbitmq_message_for_comment_insert on comments")
    op.execute("drop function send_rabbitmq_message_for_comment")

    op.execute("drop function send_rabbitmq_message")


def downgrade():
    op.execute(
        """
        CREATE OR REPLACE FUNCTION send_rabbitmq_message(routing_key TEXT, message TEXT) RETURNS VOID AS $$
            SELECT pg_notify('pgsql_events', routing_key || '|' || message);
        $$ LANGUAGE SQL;
    """
    )

    # comments
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


        CREATE TRIGGER send_rabbitmq_message_for_comment_insert
            AFTER INSERT ON comments
            FOR EACH ROW
            EXECUTE PROCEDURE send_rabbitmq_message_for_comment('created');


        CREATE TRIGGER send_rabbitmq_message_for_comment_edit
            AFTER UPDATE ON comments
            FOR EACH ROW
            WHEN (OLD.markdown IS DISTINCT FROM NEW.markdown)
            EXECUTE PROCEDURE send_rabbitmq_message_for_comment('edited');


        CREATE TRIGGER send_rabbitmq_message_for_comment_delete
            AFTER UPDATE ON comments
            FOR EACH ROW
            WHEN (OLD.is_deleted = false AND NEW.is_deleted = true)
            EXECUTE PROCEDURE send_rabbitmq_message_for_comment('deleted');


        CREATE TRIGGER send_rabbitmq_message_for_comment_undelete
            AFTER UPDATE ON comments
            FOR EACH ROW
            WHEN (OLD.is_deleted = true AND NEW.is_deleted = false)
            EXECUTE PROCEDURE send_rabbitmq_message_for_comment('undeleted');


        CREATE TRIGGER send_rabbitmq_message_for_comment_remove
            AFTER UPDATE ON comments
            FOR EACH ROW
            WHEN (OLD.is_removed = false AND NEW.is_removed = true)
            EXECUTE PROCEDURE send_rabbitmq_message_for_comment('removed');


        CREATE TRIGGER send_rabbitmq_message_for_comment_unremove
            AFTER UPDATE ON comments
            FOR EACH ROW
            WHEN (OLD.is_removed = true AND NEW.is_removed = false)
            EXECUTE PROCEDURE send_rabbitmq_message_for_comment('unremoved');
    """
    )

    # topics
    op.execute(
        """
        CREATE OR REPLACE FUNCTION send_rabbitmq_message_for_topic() RETURNS TRIGGER AS $$
        DECLARE
            affected_row RECORD;
            payload TEXT;
        BEGIN
            IF (TG_OP = 'INSERT' OR TG_OP = 'UPDATE') THEN
                affected_row := NEW;
            ELSIF (TG_OP = 'DELETE') THEN
                affected_row := OLD;
            END IF;

            payload := json_build_object('topic_id', affected_row.topic_id);

            PERFORM send_rabbitmq_message('topic.' || TG_ARGV[0], payload);

            RETURN NULL;
        END;
        $$ LANGUAGE plpgsql;


        CREATE TRIGGER send_rabbitmq_message_for_topic_insert
            AFTER INSERT ON topics
            FOR EACH ROW
            EXECUTE PROCEDURE send_rabbitmq_message_for_topic('created');


        CREATE TRIGGER send_rabbitmq_message_for_topic_edit
            AFTER UPDATE ON topics
            FOR EACH ROW
            WHEN (OLD.markdown IS DISTINCT FROM NEW.markdown)
            EXECUTE PROCEDURE send_rabbitmq_message_for_topic('edited');


        CREATE TRIGGER send_rabbitmq_message_for_topic_link_edit
            AFTER UPDATE ON topics
            FOR EACH ROW
            WHEN (OLD.link IS DISTINCT FROM NEW.link)
            EXECUTE PROCEDURE send_rabbitmq_message_for_topic('link_edited');
    """
    )

    # comment_labels
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


        CREATE TRIGGER send_rabbitmq_message_for_comment_label_insert
            AFTER INSERT ON comment_labels
            FOR EACH ROW
            EXECUTE PROCEDURE send_rabbitmq_message_for_comment_label('created');


        CREATE TRIGGER send_rabbitmq_message_for_comment_label_delete
            AFTER DELETE ON comment_labels
            FOR EACH ROW
            EXECUTE PROCEDURE send_rabbitmq_message_for_comment_label('deleted');
    """
    )

    # scraper_results
    op.execute(
        """
        CREATE OR REPLACE FUNCTION send_rabbitmq_message_for_scraper_result() RETURNS TRIGGER AS $$
        DECLARE
            affected_row RECORD;
            payload TEXT;
        BEGIN
            IF (TG_OP = 'INSERT' OR TG_OP = 'UPDATE') THEN
                affected_row := NEW;
            ELSIF (TG_OP = 'DELETE') THEN
                affected_row := OLD;
            END IF;

            payload := json_build_object('result_id', affected_row.result_id);

            PERFORM send_rabbitmq_message('scraper_result.' || TG_ARGV[0], payload);

            RETURN NULL;
        END;
        $$ LANGUAGE plpgsql;


        CREATE TRIGGER send_rabbitmq_message_for_scraper_result_insert
            AFTER INSERT ON scraper_results
            FOR EACH ROW
            EXECUTE PROCEDURE send_rabbitmq_message_for_scraper_result('created');
    """
    )
