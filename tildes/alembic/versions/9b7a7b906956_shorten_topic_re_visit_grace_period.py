"""Shorten topic re-visit grace period

Revision ID: 9b7a7b906956
Revises: 4241b0202fd4
Create Date: 2020-02-07 18:45:43.867078

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "9b7a7b906956"
down_revision = "4241b0202fd4"
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
                    and visit_time >= now() - interval '30 seconds';

            if (FOUND) then
                return null;
            else
                return NEW;
            end if;
        end;
        $$ language plpgsql;
    """
    )


def downgrade():
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
