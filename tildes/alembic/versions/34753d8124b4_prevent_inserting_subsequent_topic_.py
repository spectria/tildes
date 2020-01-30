"""Prevent inserting subsequent topic_visits

Revision ID: 34753d8124b4
Revises: 19400b1efe8b
Create Date: 2020-01-30 19:37:55.095357

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "34753d8124b4"
down_revision = "19400b1efe8b"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        """
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
    """
    )

    op.execute(
        """
        create trigger prevent_recent_repeat_visits_insert
            before insert on topic_visits
            for each row
            execute procedure prevent_recent_repeat_visits();
    """
    )


def downgrade():
    op.execute("drop trigger prevent_recent_repeat_visits_insert on topic_visits")
    op.execute("drop function prevent_recent_repeat_visits")
