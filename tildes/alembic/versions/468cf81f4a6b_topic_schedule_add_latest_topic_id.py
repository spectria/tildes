"""topic_schedule: add latest_topic_id

Revision ID: 468cf81f4a6b
Revises: 4d86b372a8db
Create Date: 2020-06-25 02:53:09.435947

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "468cf81f4a6b"
down_revision = "4d86b372a8db"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "topic_schedule", sa.Column("latest_topic_id", sa.Integer(), nullable=True)
    )
    op.create_foreign_key(
        op.f("fk_topic_schedule_latest_topic_id_topics"),
        "topic_schedule",
        "topics",
        ["latest_topic_id"],
        ["topic_id"],
    )

    op.execute(
        """
        update topic_schedule set latest_topic_id = (
            select topic_id from topics
            where schedule_id = topic_schedule.schedule_id
            order by created_time desc limit 1
        )
    """
    )

    op.execute(
        """
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
    """
    )

    op.execute(
        """
        create trigger update_topic_schedule_latest_topic_id_insert
            after insert on topics
            for each row
            when (NEW.schedule_id is not null)
            execute procedure update_topic_schedule_latest_topic_id();
    """
    )

    op.execute(
        """
        create trigger update_topic_schedule_latest_topic_id_update
            after update on topics
            for each row
            when ((OLD.schedule_id is not null or NEW.schedule_id is not null)
                and ((OLD.is_deleted is distinct from NEW.is_deleted)
                    or (OLD.is_removed is distinct from NEW.is_removed)
                    or (OLD.schedule_id is distinct from NEW.schedule_id)))
            execute procedure update_topic_schedule_latest_topic_id();
    """
    )


def downgrade():
    op.execute("drop trigger update_topic_schedule_latest_topic_id_update on topics")
    op.execute("drop trigger update_topic_schedule_latest_topic_id_insert on topics")
    op.execute("drop function update_topic_schedule_latest_topic_id")

    op.drop_constraint(
        op.f("fk_topic_schedule_latest_topic_id_topics"),
        "topic_schedule",
        type_="foreignkey",
    )
    op.drop_column("topic_schedule", "latest_topic_id")
