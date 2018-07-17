-- delete any comment notifications related to a comment when it's deleted
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
    WHEN (OLD.is_deleted = false AND NEW.is_deleted = true)
    EXECUTE PROCEDURE delete_comment_notifications();
