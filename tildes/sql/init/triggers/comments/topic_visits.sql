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


-- decrement all users' topic visit comment counts when a comment is deleted
CREATE OR REPLACE FUNCTION decrement_all_topic_visit_num_comments() RETURNS TRIGGER AS $$
BEGIN
    UPDATE topic_visits
        SET num_comments = num_comments - 1
        WHERE topic_id = OLD.topic_id AND
            visit_time > OLD.created_time;

    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_topic_visits_num_comments_update
    AFTER UPDATE ON comments
    FOR EACH ROW
    WHEN (OLD.is_deleted = false AND NEW.is_deleted = true)
    EXECUTE PROCEDURE decrement_all_topic_visit_num_comments();
