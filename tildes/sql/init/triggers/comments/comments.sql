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

CREATE TRIGGER comment_update_search_tsv_insert
    BEFORE INSERT ON comments
    FOR EACH ROW
    EXECUTE PROCEDURE tsvector_update_trigger(search_tsv, 'pg_catalog.english', markdown);

CREATE TRIGGER comment_update_search_tsv_update
    BEFORE UPDATE ON comments
    FOR EACH ROW
    WHEN (OLD.markdown IS DISTINCT FROM NEW.markdown)
    EXECUTE PROCEDURE tsvector_update_trigger(search_tsv, 'pg_catalog.english', markdown);
