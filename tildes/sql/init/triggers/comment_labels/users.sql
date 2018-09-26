-- Copyright (c) 2018 Tildes contributors <code@tildes.net>
-- SPDX-License-Identifier: AGPL-3.0-or-later

CREATE OR REPLACE FUNCTION update_user_last_exemplary_label_time() RETURNS TRIGGER AS $$
BEGIN
    UPDATE users
        SET last_exemplary_label_time = NOW()
        WHERE user_id = NEW.user_id;

    RETURN NULL;
END
$$ LANGUAGE plpgsql;


CREATE TRIGGER update_user_last_exemplary_label_time
    AFTER INSERT ON comment_labels
    FOR EACH ROW
    WHEN (NEW.label = 'EXEMPLARY')
    EXECUTE PROCEDURE update_user_last_exemplary_label_time();
