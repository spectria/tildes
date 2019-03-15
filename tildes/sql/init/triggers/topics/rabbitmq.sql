-- Copyright (c) 2018 Tildes contributors <code@tildes.net>
-- SPDX-License-Identifier: AGPL-3.0-or-later

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
