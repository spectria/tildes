-- set topic.deleted_time when it's deleted
CREATE OR REPLACE FUNCTION set_topic_deleted_time() RETURNS TRIGGER AS $$
BEGIN
    NEW.deleted_time := current_timestamp;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER delete_topic_set_deleted_time_update
    BEFORE UPDATE ON topics
    FOR EACH ROW
    WHEN (OLD.is_deleted = false AND NEW.is_deleted = true)
    EXECUTE PROCEDURE set_topic_deleted_time();


CREATE TRIGGER topic_update_search_tsv_insert
    BEFORE INSERT ON topics
    FOR EACH ROW
    EXECUTE PROCEDURE tsvector_update_trigger(search_tsv, 'pg_catalog.english', title, markdown);

CREATE TRIGGER topic_update_search_tsv_update
    BEFORE UPDATE ON topics
    FOR EACH ROW
    WHEN (
        (OLD.title IS DISTINCT FROM NEW.title)
        OR (OLD.markdown IS DISTINCT FROM NEW.markdown)
    )
    EXECUTE PROCEDURE tsvector_update_trigger(search_tsv, 'pg_catalog.english', title, markdown);
