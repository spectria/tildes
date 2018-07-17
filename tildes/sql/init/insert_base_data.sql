-- add an "unknown user" for re-assigning deleted comments to after they're
-- outside the retention period, and similar uses
INSERT INTO users (user_id, username, password_hash)
VALUES (0, 'unknown user', '');
