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
