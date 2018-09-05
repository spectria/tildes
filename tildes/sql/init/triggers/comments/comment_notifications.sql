-- Copyright (c) 2018 Tildes contributors <code@tildes.net>
-- SPDX-License-Identifier: AGPL-3.0-or-later

-- delete any notifications related to a comment when it's deleted or removed
CREATE OR REPLACE FUNCTION delete_comment_notifications() RETURNS TRIGGER AS $$
BEGIN
    DELETE FROM comment_notifications
        WHERE comment_id = OLD.comment_id;

    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER delete_comment_notifications_update
    AFTER UPDATE ON comments
    FOR EACH ROW
    WHEN ((OLD.is_deleted = false AND NEW.is_deleted = true)
        OR (OLD.is_removed = false AND NEW.is_removed = true))
    EXECUTE PROCEDURE delete_comment_notifications();
