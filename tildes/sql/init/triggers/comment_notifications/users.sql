-- Copyright (c) 2018 Tildes contributors <code@tildes.net>
-- SPDX-License-Identifier: AGPL-3.0-or-later

CREATE OR REPLACE FUNCTION update_users_num_unread_notifications() RETURNS TRIGGER AS $$
BEGIN
    IF (TG_OP = 'INSERT') THEN
        UPDATE users
            SET num_unread_notifications = num_unread_notifications + 1
            WHERE user_id = NEW.user_id;
    ELSIF (TG_OP = 'DELETE') THEN
        IF (OLD.is_unread = TRUE) THEN
            UPDATE users
                SET num_unread_notifications = num_unread_notifications - 1
                WHERE user_id = OLD.user_id;
        END IF;
    ELSIF (TG_OP = 'UPDATE') THEN
        IF (OLD.is_unread = FALSE AND NEW.is_unread = TRUE) THEN
            UPDATE users
                SET num_unread_notifications = num_unread_notifications + 1
                WHERE user_id = NEW.user_id;
        ELSIF (OLD.is_unread = TRUE AND NEW.is_unread = FALSE) THEN
            UPDATE users
                SET num_unread_notifications = num_unread_notifications - 1
                WHERE user_id = NEW.user_id;
        END IF;
    END IF;

    RETURN NULL;
END
$$ LANGUAGE plpgsql;


-- insert and delete triggers should execute unconditionally
CREATE TRIGGER update_users_num_unread_notifications_insert_delete
    AFTER INSERT OR DELETE ON comment_notifications
    FOR EACH ROW
    EXECUTE PROCEDURE update_users_num_unread_notifications();


-- update trigger only needs to execute if is_unread was changed
CREATE TRIGGER update_users_num_unread_notifications_update
    AFTER UPDATE ON comment_notifications
    FOR EACH ROW
    WHEN (OLD.is_unread IS DISTINCT FROM NEW.is_unread)
    EXECUTE PROCEDURE update_users_num_unread_notifications();
