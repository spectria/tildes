-- Copyright (c) 2018 Tildes contributors <code@tildes.net>
-- SPDX-License-Identifier: AGPL-3.0-or-later

CREATE OR REPLACE FUNCTION update_group_subscription_count() RETURNS TRIGGER AS $$
BEGIN
    IF (TG_OP = 'INSERT') THEN
        UPDATE groups
            SET num_subscriptions = num_subscriptions + 1
            WHERE group_id = NEW.group_id;
    ELSIF (TG_OP = 'DELETE') THEN
        UPDATE groups
            SET num_subscriptions = num_subscriptions - 1
            WHERE group_id = OLD.group_id;
    END IF;

    RETURN NULL;
END
$$ LANGUAGE plpgsql;


CREATE TRIGGER update_group_subscription_count
    AFTER INSERT OR DELETE ON group_subscriptions
    FOR EACH ROW
    EXECUTE PROCEDURE update_group_subscription_count();
