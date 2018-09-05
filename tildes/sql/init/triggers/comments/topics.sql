-- Copyright (c) 2018 Tildes contributors <code@tildes.net>
-- SPDX-License-Identifier: AGPL-3.0-or-later

CREATE OR REPLACE FUNCTION update_topics_num_comments() RETURNS TRIGGER AS $$
BEGIN
    IF (TG_OP = 'INSERT') THEN
        UPDATE topics
            SET num_comments = num_comments + 1
            WHERE topic_id = NEW.topic_id;
    ELSIF (TG_OP = 'DELETE'
            AND OLD.is_deleted = FALSE
            AND OLD.is_removed = FALSE) THEN
        UPDATE topics
            SET num_comments = num_comments - 1
            WHERE topic_id = OLD.topic_id;
    ELSIF (TG_OP = 'UPDATE') THEN
        DECLARE
            old_visible BOOLEAN := NOT (OLD.is_deleted OR OLD.is_removed);
            new_visible BOOLEAN := NOT (NEW.is_deleted OR NEW.is_removed);
        BEGIN
            IF (old_visible AND NOT new_visible) THEN
                UPDATE topics
                    SET num_comments = num_comments - 1
                    WHERE topic_id = NEW.topic_id;
            ELSIF (NOT old_visible AND new_visible) THEN
                UPDATE topics
                    SET num_comments = num_comments + 1
                    WHERE topic_id = NEW.topic_id;
            END IF;
        END;
    END IF;

    RETURN NULL;
END;
$$ LANGUAGE plpgsql;


-- insert and delete triggers should execute unconditionally
CREATE TRIGGER update_topics_num_comments_insert_delete
    AFTER INSERT OR DELETE ON comments
    FOR EACH ROW
    EXECUTE PROCEDURE update_topics_num_comments();


-- update trigger only needs to execute if is_deleted or is_removed was changed
CREATE TRIGGER update_topics_num_comments_update
    AFTER UPDATE ON comments
    FOR EACH ROW
    WHEN ((OLD.is_deleted IS DISTINCT FROM NEW.is_deleted)
        OR (OLD.is_removed IS DISTINCT FROM NEW.is_removed))
    EXECUTE PROCEDURE update_topics_num_comments();


-- update a topic's last activity time when a comment is posted, deleted, or removed
CREATE OR REPLACE FUNCTION update_topics_last_activity_time() RETURNS TRIGGER AS $$
DECLARE
    most_recent_comment RECORD;
BEGIN
    IF (TG_OP = 'INSERT') THEN
        UPDATE topics
            SET last_activity_time = NOW()
            WHERE topic_id = NEW.topic_id;
    ELSIF (TG_OP = 'UPDATE') THEN
        SELECT MAX(created_time) AS max_created_time
        INTO most_recent_comment
        FROM comments
        WHERE topic_id = NEW.topic_id
            AND is_deleted = FALSE
            AND is_removed = FALSE;

        IF most_recent_comment.max_created_time IS NOT NULL THEN
            UPDATE topics
                SET last_activity_time = most_recent_comment.max_created_time
                WHERE topic_id = NEW.topic_id;
        ELSE
            UPDATE topics
                SET last_activity_time = created_time
                WHERE topic_id = NEW.topic_id;
        END IF;
    END IF;

    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_topics_last_activity_time_insert
    AFTER INSERT ON comments
    FOR EACH ROW
    EXECUTE PROCEDURE update_topics_last_activity_time();

CREATE TRIGGER update_topics_last_activity_time_update
    AFTER UPDATE ON comments
    FOR EACH ROW
    WHEN ((OLD.is_deleted IS DISTINCT FROM NEW.is_deleted)
        OR (OLD.is_removed IS DISTINCT FROM NEW.is_removed))
    EXECUTE PROCEDURE update_topics_last_activity_time();
