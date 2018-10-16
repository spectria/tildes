-- Copyright (c) 2018 Tildes contributors <code@tildes.net>
-- SPDX-License-Identifier: AGPL-3.0-or-later

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


CREATE OR REPLACE FUNCTION update_topic_search_tsv() RETURNS TRIGGER AS $$
BEGIN
    NEW.search_tsv :=
        to_tsvector(NEW.title) ||
        to_tsvector(coalesce(NEW.markdown, '')) ||
        -- convert tags to space-separated string and replace periods with spaces
        to_tsvector(replace(array_to_string(NEW.tags, ' '), '.', ' '));

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;


CREATE TRIGGER topic_update_search_tsv_insert
    BEFORE INSERT ON topics
    FOR EACH ROW
    EXECUTE PROCEDURE update_topic_search_tsv();

CREATE TRIGGER topic_update_search_tsv_update
    BEFORE UPDATE ON topics
    FOR EACH ROW
    WHEN (
        (OLD.title IS DISTINCT FROM NEW.title)
        OR (OLD.markdown IS DISTINCT FROM NEW.markdown)
        OR (OLD.tags IS DISTINCT FROM NEW.tags)
    )
    EXECUTE PROCEDURE update_topic_search_tsv();
