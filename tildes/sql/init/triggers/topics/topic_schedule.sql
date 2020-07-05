-- Copyright (c) 2020 Tildes contributors <code@tildes.net>
-- SPDX-License-Identifier: AGPL-3.0-or-later

create or replace function update_topic_schedule_latest_topic_id() returns trigger as $$
begin
    if (NEW.schedule_id is not null) then
        update topic_schedule
            set latest_topic_id = (
                select topic_id
                    from topics
                    where schedule_id = NEW.schedule_id
                        and is_deleted = false
                        and is_removed = false
                    order by created_time desc limit 1)
            where schedule_id = NEW.schedule_id;
    end if;

    -- if it was an update that changed schedule_id, need to update the old schedule's
    -- latest_topic_id as well (this will probably be extremely uncommon)
    if (TG_OP = 'UPDATE'
            and OLD.schedule_id is not null
            and OLD.schedule_id is distinct from NEW.schedule_id) then
        update topic_schedule
            set latest_topic_id = (
                select topic_id
                    from topics
                    where schedule_id = OLD.schedule_id
                        and is_deleted = false
                        and is_removed = false
                    order by created_time desc limit 1)
            where schedule_id = OLD.schedule_id;
    end if;

    return null;
end
$$ language plpgsql;


create trigger update_topic_schedule_latest_topic_id_insert
    after insert on topics
    for each row
    when (NEW.schedule_id is not null)
    execute procedure update_topic_schedule_latest_topic_id();


create trigger update_topic_schedule_latest_topic_id_update
    after update on topics
    for each row
    when ((OLD.schedule_id is not null or NEW.schedule_id is not null)
        and ((OLD.is_deleted is distinct from NEW.is_deleted)
            or (OLD.is_removed is distinct from NEW.is_removed)
            or (OLD.schedule_id is distinct from NEW.schedule_id)))
    execute procedure update_topic_schedule_latest_topic_id();
