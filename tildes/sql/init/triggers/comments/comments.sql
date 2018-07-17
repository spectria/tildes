-- set comment.deleted_time when it's deleted
CREATE OR REPLACE FUNCTION set_comment_deleted_time() RETURNS TRIGGER AS $$
BEGIN
    NEW.deleted_time := current_timestamp;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER delete_comment_set_deleted_time_update
    BEFORE UPDATE ON comments
    FOR EACH ROW
    WHEN (OLD.is_deleted = false AND NEW.is_deleted = true)
    EXECUTE PROCEDURE set_comment_deleted_time();
