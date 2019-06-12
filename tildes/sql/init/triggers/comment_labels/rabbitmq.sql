-- Copyright (c) 2019 Tildes contributors <code@tildes.net>
-- SPDX-License-Identifier: AGPL-3.0-or-later

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
