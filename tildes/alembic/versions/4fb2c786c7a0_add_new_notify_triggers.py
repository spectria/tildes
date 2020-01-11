"""Add new NOTIFY triggers

Revision ID: 4fb2c786c7a0
Revises: f4e1ef359307
Create Date: 2020-01-19 19:45:32.460821

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "4fb2c786c7a0"
down_revision = "f4e1ef359307"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        """
        create or replace function add_to_event_stream(stream_name_pieces text[], fields text[]) returns void as $$
            select pg_notify(
                'postgresql_events',
                array_to_string(stream_name_pieces, '.') || ':' || json_object(fields)
            );
        $$ language sql;
    """
    )

    # comments
    op.execute(
        """
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
    """
    )

    # topics
    op.execute(
        """
        create or replace function topics_events_trigger() returns trigger as $$
        declare
            affected_row record := coalesce(NEW, OLD);
            stream_name_pieces text[] := array[TG_TABLE_NAME, lower(TG_OP)]::text[] || TG_ARGV;

            -- in general, only the below declaration of payload_fields should be edited
            payload_fields text[] := array[
                'topic_id', affected_row.topic_id
            ]::text[];
        begin
            perform add_to_event_stream(stream_name_pieces, payload_fields);

            return null;
        end;
        $$ language plpgsql;

        create trigger topics_events_insert_delete
            after insert or delete on topics
            for each row
            execute function topics_events_trigger();

        create trigger topics_events_update_markdown
            after update of markdown on topics
            for each row
            execute function topics_events_trigger('markdown');

        create trigger topics_events_update_link
            after update of link on topics
            for each row
            execute function topics_events_trigger('link');
    """
    )

    # comment_labels
    op.execute(
        """
        create or replace function comment_labels_events_trigger() returns trigger as $$
        declare
            affected_row record := coalesce(NEW, OLD);
            stream_name_pieces text[] := array[TG_TABLE_NAME, lower(TG_OP)]::text[] || TG_ARGV;

            -- in general, only the below declaration of payload_fields should be edited
            payload_fields text[] := array[
                'comment_id', affected_row.comment_id,
                'user_id', affected_row.user_id,
                'label', affected_row.label
            ]::text[];
        begin
            perform add_to_event_stream(stream_name_pieces, payload_fields);

            return null;
        end;
        $$ language plpgsql;

        create trigger comment_labels_events_insert_delete
            after insert or delete on comment_labels
            for each row
            execute function comment_labels_events_trigger();
    """
    )

    # scraper_results
    op.execute(
        """
        create or replace function scraper_results_events_trigger() returns trigger as $$
        declare
            affected_row record := coalesce(NEW, OLD);
            stream_name_pieces text[] := array[TG_TABLE_NAME, lower(TG_OP)]::text[] || TG_ARGV;

            -- in general, only the below declaration of payload_fields should be edited
            payload_fields text[] := array[
                'result_id', affected_row.result_id
            ]::text[];
        begin
            perform add_to_event_stream(stream_name_pieces, payload_fields);

            return null;
        end;
        $$ language plpgsql;

        create trigger scraper_results_events_insert_delete
            after insert or delete on scraper_results
            for each row
            execute function scraper_results_events_trigger();
    """
    )


def downgrade():
    op.execute("drop trigger scraper_results_events_insert_delete on scraper_results")
    op.execute("drop function scraper_results_events_trigger")

    op.execute("drop trigger comment_labels_events_insert_delete on comment_labels")
    op.execute("drop function comment_labels_events_trigger")

    op.execute("drop trigger topics_events_update_link on topics")
    op.execute("drop trigger topics_events_update_markdown on topics")
    op.execute("drop trigger topics_events_insert_delete on topics")
    op.execute("drop function topics_events_trigger")

    op.execute("drop trigger comments_events_update_is_removed on comments")
    op.execute("drop trigger comments_events_update_is_deleted on comments")
    op.execute("drop trigger comments_events_update_markdown on comments")
    op.execute("drop trigger comments_events_insert_delete on comments")
    op.execute("drop function comments_events_trigger")

    op.execute("drop function add_to_event_stream")
