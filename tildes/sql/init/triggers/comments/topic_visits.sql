-- Copyright (c) 2018 Tildes contributors <code@tildes.net>
-- SPDX-License-Identifier: AGPL-3.0-or-later

-- increment a user's topic visit comment count when they post a comment
CREATE OR REPLACE FUNCTION increment_user_topic_visit_num_comments() RETURNS TRIGGER AS $$
BEGIN
    UPDATE topic_visits
        SET num_comments = num_comments + 1
        WHERE user_id = NEW.user_id
            AND topic_id = NEW.topic_id;

    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_topic_visits_num_comments_insert
    AFTER INSERT ON comments
    FOR EACH ROW
    EXECUTE PROCEDURE increment_user_topic_visit_num_comments();


-- adjust all users' topic visit comment counts when a comment is deleted/removed
CREATE OR REPLACE FUNCTION update_all_topic_visit_num_comments() RETURNS TRIGGER AS $$
DECLARE
    old_visible BOOLEAN := NOT (OLD.is_deleted OR OLD.is_removed);
    new_visible BOOLEAN := NOT (NEW.is_deleted OR NEW.is_removed);
BEGIN
    IF (old_visible AND NOT new_visible) THEN
        UPDATE topic_visits
            SET num_comments = num_comments - 1
            WHERE topic_id = OLD.topic_id AND
                visit_time > OLD.created_time;
    ELSIF (NOT old_visible AND new_visible) THEN
        UPDATE topic_visits
            SET num_comments = num_comments + 1
            WHERE topic_id = OLD.topic_id AND
                visit_time > OLD.created_time;
    END IF;

    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_topic_visits_num_comments_update
    AFTER UPDATE ON comments
    FOR EACH ROW
    WHEN ((OLD.is_deleted IS DISTINCT FROM NEW.is_deleted)
        OR (OLD.is_removed IS DISTINCT FROM NEW.is_removed))
    EXECUTE PROCEDURE update_all_topic_visit_num_comments();
