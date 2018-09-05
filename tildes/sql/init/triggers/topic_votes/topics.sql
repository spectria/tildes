-- Copyright (c) 2018 Tildes contributors <code@tildes.net>
-- SPDX-License-Identifier: AGPL-3.0-or-later

CREATE OR REPLACE FUNCTION update_topic_num_votes() RETURNS TRIGGER AS $$
BEGIN
    IF (TG_OP = 'INSERT') THEN
        UPDATE topics
            SET num_votes = num_votes + 1
            WHERE topic_id = NEW.topic_id;
    ELSIF (TG_OP = 'DELETE') THEN
        UPDATE topics
            SET num_votes = num_votes - 1
            WHERE topic_id = OLD.topic_id;
    END IF;

    RETURN NULL;
END
$$ LANGUAGE plpgsql;


CREATE TRIGGER update_topic_num_votes
    AFTER INSERT OR DELETE ON topic_votes
    FOR EACH ROW
    EXECUTE PROCEDURE update_topic_num_votes();
