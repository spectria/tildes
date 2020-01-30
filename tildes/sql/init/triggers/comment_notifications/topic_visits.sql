-- Copyright (c) 2020 Tildes contributors <code@tildes.net>
-- SPDX-License-Identifier: AGPL-3.0-or-later

create or replace function update_last_topic_visit_num_comments() returns trigger as $$
declare
    comment comments%rowtype;
begin
    select * INTO comment from comments where comment_id = NEW.comment_id;

    -- if marking a notification as read, increment the comment count on the user's
    -- last visit to the topic as long as it was before the comment was posted
    if (OLD.is_unread = true and NEW.is_unread = false) then
        update topic_visits
            set num_comments = num_comments + 1
            where topic_id = comment.topic_id
                and user_id = NEW.user_id
                and visit_time < comment.created_time
                and visit_time = (
                    select max(visit_time)
                    from topic_visits
                    where topic_id = comment.topic_id
                        and user_id = NEW.user_id
                );
    end if;

    return null;
end
$$ language plpgsql;


create trigger update_last_topic_visit_num_comments_update
    after update of is_unread on comment_notifications
    for each row
    execute procedure update_last_topic_visit_num_comments();
