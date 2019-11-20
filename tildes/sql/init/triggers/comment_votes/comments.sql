-- Copyright (c) 2018 Tildes contributors <code@tildes.net>
-- SPDX-License-Identifier: AGPL-3.0-or-later

CREATE OR REPLACE FUNCTION update_comment_num_votes() RETURNS TRIGGER AS $$
BEGIN
    IF (TG_OP = 'INSERT') THEN
        UPDATE comments
            SET num_votes = num_votes + 1
            WHERE comment_id = NEW.comment_id;
    ELSIF (TG_OP = 'DELETE') THEN
        -- Exclude comments with closed voting from decrements so that individual vote
        -- records can be deleted while retaining the final vote total.
        UPDATE comments
            SET num_votes = num_votes - 1
            WHERE comment_id = OLD.comment_id
                AND is_voting_closed = FALSE;
    END IF;

    RETURN NULL;
END
$$ LANGUAGE plpgsql;


CREATE TRIGGER update_comment_num_votes
    AFTER INSERT OR DELETE ON comment_votes
    FOR EACH ROW
    EXECUTE PROCEDURE update_comment_num_votes();
