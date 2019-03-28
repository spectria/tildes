-- Copyright (c) 2018 Tildes contributors <code@tildes.net>
-- SPDX-License-Identifier: AGPL-3.0-or-later

-- set user.deleted_time when it's deleted
CREATE OR REPLACE FUNCTION set_user_deleted_time() RETURNS TRIGGER AS $$
BEGIN
    NEW.deleted_time := current_timestamp;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER delete_user_set_deleted_time_update
    BEFORE UPDATE ON users
    FOR EACH ROW
    WHEN (OLD.is_deleted = false AND NEW.is_deleted = true)
    EXECUTE PROCEDURE set_user_deleted_time();


-- set user.banned_time when it's banned
CREATE OR REPLACE FUNCTION set_user_banned_time() RETURNS TRIGGER AS $$
BEGIN
    NEW.banned_time := current_timestamp;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER ban_user_set_banned_time_update
    BEFORE UPDATE ON users
    FOR EACH ROW
    WHEN (OLD.is_banned = false AND NEW.is_banned = true)
    EXECUTE PROCEDURE set_user_banned_time();
