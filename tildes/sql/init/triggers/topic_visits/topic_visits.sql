-- Copyright (c) 2020 Tildes contributors <code@tildes.net>
-- SPDX-License-Identifier: AGPL-3.0-or-later

-- prevent inserting another visit immediately after an existing one
create or replace function prevent_recent_repeat_visits() returns trigger as $$
begin
    perform * from topic_visits
        where user_id = NEW.user_id
            and topic_id = NEW.topic_id
            and visit_time >= now() - interval '2 minutes';

    if (FOUND) then
        return null;
    else
        return NEW;
    end if;
end;
$$ language plpgsql;


create trigger prevent_recent_repeat_visits_insert
    before insert on topic_visits
    for each row
    execute procedure prevent_recent_repeat_visits();
