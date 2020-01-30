"""Add visit_time to topic_visits primary key

Revision ID: 19400b1efe8b
Revises: 6c840340ab86
Create Date: 2020-01-30 00:14:47.511461

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "19400b1efe8b"
down_revision = "6c840340ab86"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("alter table topic_visits drop constraint pk_topic_visits")
    op.execute(
        "alter table topic_visits add constraint pk_topic_visits primary key (user_id, topic_id, visit_time)"
    )
    op.alter_column("topic_visits", "visit_time", server_default=sa.text("NOW()"))

    op.execute(
        """
        CREATE OR REPLACE FUNCTION increment_user_topic_visit_num_comments() RETURNS TRIGGER AS $$
        BEGIN
            UPDATE topic_visits
                SET num_comments = num_comments + 1
                WHERE user_id = NEW.user_id
                    AND topic_id = NEW.topic_id
                    AND visit_time = (
                        SELECT MAX(visit_time)
                        FROM topic_visits
                        WHERE topic_id = NEW.topic_id
                            AND user_id = NEW.user_id
                    );

            RETURN NULL;
        END;
        $$ LANGUAGE plpgsql;
    """
    )

    op.execute(
        """
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
    """
    )

    op.execute(
        """
        create trigger update_last_topic_visit_num_comments_update
            after update of is_unread on comment_notifications
            for each row
            execute procedure update_last_topic_visit_num_comments();
    """
    )


def downgrade():
    op.execute("alter table topic_visits drop constraint pk_topic_visits")
    op.execute(
        "alter table topic_visits add constraint pk_topic_visits primary key (user_id, topic_id)"
    )
    op.alter_column("topic_visits", "visit_time", server_default=None)

    op.execute(
        "drop trigger update_last_topic_visit_num_comments_update on comment_notifications"
    )
    op.execute("drop function update_last_topic_visit_num_comments")

    op.execute(
        """
        CREATE OR REPLACE FUNCTION increment_user_topic_visit_num_comments() RETURNS TRIGGER AS $$
        BEGIN
            UPDATE topic_visits
                SET num_comments = num_comments + 1
                WHERE user_id = NEW.user_id
                    AND topic_id = NEW.topic_id;

            RETURN NULL;
        END;
        $$ LANGUAGE plpgsql;
    """
    )
