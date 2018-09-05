-- Copyright (c) 2018 Tildes contributors <code@tildes.net>
-- SPDX-License-Identifier: AGPL-3.0-or-later

-- set comment.deleted_time when is_deleted changes
CREATE OR REPLACE FUNCTION set_comment_deleted_time() RETURNS TRIGGER AS $$
BEGIN
    IF (NEW.is_deleted = TRUE) THEN
        NEW.deleted_time := current_timestamp;
    ELSE
        NEW.deleted_time := NULL;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER delete_comment_set_deleted_time_update
    BEFORE UPDATE ON comments
    FOR EACH ROW
    WHEN (OLD.is_deleted IS DISTINCT FROM NEW.is_deleted)
    EXECUTE PROCEDURE set_comment_deleted_time();
