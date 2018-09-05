-- Copyright (c) 2018 Tildes contributors <code@tildes.net>
-- SPDX-License-Identifier: AGPL-3.0-or-later

CREATE OR REPLACE FUNCTION update_conversation() RETURNS TRIGGER AS $$
BEGIN
    IF (TG_OP = 'INSERT') THEN
        -- Increment num_replies and set last_reply_time to the new reply's
        -- created_time, and use a CASE statement to union the id of the
        -- "other user" (not the sender) into the unread ids
        UPDATE message_conversations
            SET num_replies = num_replies + 1,
                last_reply_time = NEW.created_time,
                unread_user_ids = unread_user_ids |
                    CASE WHEN sender_id = NEW.sender_id THEN recipient_id
                        ELSE sender_id
                    END
            WHERE conversation_id = NEW.conversation_id;
    ELSIF (TG_OP = 'DELETE') THEN
        -- Decrement num_replies and use a subselect to get the created_time
        -- for the most recent reply. This isn't necessary when the deleted
        -- reply wasn't the newest one, but it won't hurt anything either.
        UPDATE message_conversations
            SET num_replies = num_replies - 1,
                last_reply_time = (
                    SELECT MAX(created_time)
                    FROM message_replies
                    WHERE conversation_id = OLD.conversation_id
                )
            WHERE conversation_id = OLD.conversation_id;
    END IF;

    RETURN NULL;
END
$$ LANGUAGE plpgsql;


CREATE TRIGGER update_conversation
    AFTER INSERT OR DELETE ON message_replies
    FOR EACH ROW
    EXECUTE PROCEDURE update_conversation();
