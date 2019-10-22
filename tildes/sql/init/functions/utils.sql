-- Copyright (c) 2019 Tildes contributors <code@tildes.net>
-- SPDX-License-Identifier: AGPL-3.0-or-later

CREATE OR REPLACE FUNCTION id36_to_id(id36 TEXT) RETURNS INTEGER AS $$
    from tildes.lib.id import id36_to_id

    return id36_to_id(id36)
$$ IMMUTABLE LANGUAGE plpython3u;
