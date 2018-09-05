-- Copyright (c) 2018 Tildes contributors <code@tildes.net>
-- SPDX-License-Identifier: AGPL-3.0-or-later

CREATE OR REPLACE FUNCTION update_users_num_unread_messages() RETURNS TRIGGER AS $$
BEGIN
    IF (TG_OP = 'INSERT') THEN
        -- increment unread count for user(s) in the initial "unread by" list
        UPDATE users
            SET num_unread_messages = num_unread_messages + 1
            WHERE user_id = ANY(NEW.unread_user_ids);
    ELSIF (TG_OP = 'UPDATE') THEN
        -- increment unread count for any users that were added by the update
        UPDATE users
            SET num_unread_messages = num_unread_messages + 1
            WHERE user_id = ANY(NEW.unread_user_ids::int[] - OLD.unread_user_ids::int[]);

        -- decrement unread count for any users that were removed by the update
        UPDATE users
            SET num_unread_messages = num_unread_messages - 1
            WHERE user_id = ANY(OLD.unread_user_ids::int[] - NEW.unread_user_ids::int[]);
    END IF;

    RETURN NULL;
END;
$$ LANGUAGE plpgsql;


-- insert trigger should execute unconditionally
CREATE TRIGGER update_users_num_unread_messages_insert
    AFTER INSERT ON message_conversations
    FOR EACH ROW
    EXECUTE PROCEDURE update_users_num_unread_messages();


-- update trigger only needs to execute if unread_user_ids was changed
CREATE TRIGGER update_users_num_unread_messages_update
    AFTER UPDATE ON message_conversations
    FOR EACH ROW
    WHEN (OLD.unread_user_ids IS DISTINCT FROM NEW.unread_user_ids)
    EXECUTE PROCEDURE update_users_num_unread_messages();
