-- Copyright (c) 2020 Tildes contributors <code@tildes.net>
-- SPDX-License-Identifier: AGPL-3.0-or-later

create or replace function add_to_event_stream(stream_name_pieces text[], fields text[]) returns void as $$
    select pg_notify(
        'postgresql_events',
        array_to_string(stream_name_pieces, '.') || ':' || json_object(fields)
    );
$$ language sql;
