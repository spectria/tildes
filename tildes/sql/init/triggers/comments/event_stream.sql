-- Copyright (c) 2020 Tildes contributors <code@tildes.net>
-- SPDX-License-Identifier: AGPL-3.0-or-later

create or replace function comments_events_trigger() returns trigger as $$
declare
    affected_row record := coalesce(NEW, OLD);
    stream_name_pieces text[] := array[TG_TABLE_NAME, lower(TG_OP)]::text[] || TG_ARGV;

    -- in general, only the below declaration of payload_fields should be edited
    payload_fields text[] := array[
        'comment_id', affected_row.comment_id
    ]::text[];
begin
    perform add_to_event_stream(stream_name_pieces, payload_fields);

    return null;
end;
$$ language plpgsql;

create trigger comments_events_insert_delete
    after insert or delete on comments
    for each row
    execute function comments_events_trigger();

create trigger comments_events_update_markdown
    after update of markdown on comments
    for each row
    execute function comments_events_trigger('markdown');

create trigger comments_events_update_is_deleted
    after update of is_deleted on comments
    for each row
    execute function comments_events_trigger('is_deleted');

create trigger comments_events_update_is_removed
    after update of is_removed on comments
    for each row
    execute function comments_events_trigger('is_removed');
