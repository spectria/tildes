"""Update comment triggers for removals

Revision ID: fab922a8bb04
Revises: f1ecbf24c212
Create Date: 2018-08-09 00:56:40.718440

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "fab922a8bb04"
down_revision = "f1ecbf24c212"
branch_labels = None
depends_on = None


def upgrade():
    # comment_notifications
    op.execute("DROP TRIGGER delete_comment_notifications_update ON comments")
    op.execute(
        """
        CREATE TRIGGER delete_comment_notifications_update
            AFTER UPDATE ON comments
            FOR EACH ROW
            WHEN ((OLD.is_deleted = false AND NEW.is_deleted = true)
                OR (OLD.is_removed = false AND NEW.is_removed = true))
            EXECUTE PROCEDURE delete_comment_notifications();
    """
    )

    # comments
    op.execute(
        """
        CREATE OR REPLACE FUNCTION set_comment_deleted_time() RETURNS TRIGGER AS $$
        BEGIN
            IF (NEW.is_deleted = TRUE) THEN
                NEW.deleted_time := current_timestamp;
            ELSE
                NEW.deleted_time := NULL;
            END IF;

            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """
    )
    op.execute("DROP TRIGGER delete_comment_set_deleted_time_update ON comments")
    op.execute(
        """
        CREATE TRIGGER delete_comment_set_deleted_time_update
            BEFORE UPDATE ON comments
            FOR EACH ROW
            WHEN (OLD.is_deleted IS DISTINCT FROM NEW.is_deleted)
            EXECUTE PROCEDURE set_comment_deleted_time();
    """
    )

    op.execute(
        """
        CREATE OR REPLACE FUNCTION set_comment_removed_time() RETURNS TRIGGER AS $$
        BEGIN
            IF (NEW.is_removed = TRUE) THEN
                NEW.removed_time := current_timestamp;
            ELSE
                NEW.removed_time := NULL;
            END IF;

            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """
    )
    op.execute(
        """
        CREATE TRIGGER remove_comment_set_removed_time_update
            BEFORE UPDATE ON comments
            FOR EACH ROW
            WHEN (OLD.is_removed IS DISTINCT FROM NEW.is_removed)
            EXECUTE PROCEDURE set_comment_removed_time();
    """
    )

    # topic_visits
    op.execute("DROP TRIGGER update_topic_visits_num_comments_update ON comments")
    op.execute("DROP FUNCTION decrement_all_topic_visit_num_comments()")
    op.execute(
        """
        CREATE OR REPLACE FUNCTION update_all_topic_visit_num_comments() RETURNS TRIGGER AS $$
        DECLARE
            old_visible BOOLEAN := NOT (OLD.is_deleted OR OLD.is_removed);
            new_visible BOOLEAN := NOT (NEW.is_deleted OR NEW.is_removed);
        BEGIN
            IF (old_visible AND NOT new_visible) THEN
                UPDATE topic_visits
                    SET num_comments = num_comments - 1
                    WHERE topic_id = OLD.topic_id AND
                        visit_time > OLD.created_time;
            ELSIF (NOT old_visible AND new_visible) THEN
                UPDATE topic_visits
                    SET num_comments = num_comments + 1
                    WHERE topic_id = OLD.topic_id AND
                        visit_time > OLD.created_time;
            END IF;

            RETURN NULL;
        END;
        $$ LANGUAGE plpgsql;
    """
    )
    op.execute(
        """
        CREATE TRIGGER update_topic_visits_num_comments_update
            AFTER UPDATE ON comments
            FOR EACH ROW
            WHEN ((OLD.is_deleted IS DISTINCT FROM NEW.is_deleted)
                OR (OLD.is_removed IS DISTINCT FROM NEW.is_removed))
            EXECUTE PROCEDURE update_all_topic_visit_num_comments();
    """
    )

    # topics
    op.execute(
        """
        CREATE OR REPLACE FUNCTION update_topics_num_comments() RETURNS TRIGGER AS $$
        BEGIN
            IF (TG_OP = 'INSERT') THEN
                UPDATE topics
                    SET num_comments = num_comments + 1
                    WHERE topic_id = NEW.topic_id;
            ELSIF (TG_OP = 'DELETE'
                    AND OLD.is_deleted = FALSE
                    AND OLD.is_removed = FALSE) THEN
                UPDATE topics
                    SET num_comments = num_comments - 1
                    WHERE topic_id = OLD.topic_id;
            ELSIF (TG_OP = 'UPDATE') THEN
                DECLARE
                    old_visible BOOLEAN := NOT (OLD.is_deleted OR OLD.is_removed);
                    new_visible BOOLEAN := NOT (NEW.is_deleted OR NEW.is_removed);
                BEGIN
                    IF (old_visible AND NOT new_visible) THEN
                        UPDATE topics
                            SET num_comments = num_comments - 1
                            WHERE topic_id = NEW.topic_id;
                    ELSIF (NOT old_visible AND new_visible) THEN
                        UPDATE topics
                            SET num_comments = num_comments + 1
                            WHERE topic_id = NEW.topic_id;
                    END IF;
                END;
            END IF;

            RETURN NULL;
        END;
        $$ LANGUAGE plpgsql;
    """
    )
    op.execute("DROP TRIGGER update_topics_num_comments_update ON comments")
    op.execute(
        """
        CREATE TRIGGER update_topics_num_comments_update
            AFTER UPDATE ON comments
            FOR EACH ROW
            WHEN ((OLD.is_deleted IS DISTINCT FROM NEW.is_deleted)
                OR (OLD.is_removed IS DISTINCT FROM NEW.is_removed))
            EXECUTE PROCEDURE update_topics_num_comments();
    """
    )

    op.execute(
        """
        CREATE OR REPLACE FUNCTION update_topics_last_activity_time() RETURNS TRIGGER AS $$
        DECLARE
            most_recent_comment RECORD;
        BEGIN
            IF (TG_OP = 'INSERT') THEN
                UPDATE topics
                    SET last_activity_time = NOW()
                    WHERE topic_id = NEW.topic_id;
            ELSIF (TG_OP = 'UPDATE') THEN
                SELECT MAX(created_time) AS max_created_time
                INTO most_recent_comment
                FROM comments
                WHERE topic_id = NEW.topic_id
                    AND is_deleted = FALSE
                    AND is_removed = FALSE;

                IF most_recent_comment.max_created_time IS NOT NULL THEN
                    UPDATE topics
                        SET last_activity_time = most_recent_comment.max_created_time
                        WHERE topic_id = NEW.topic_id;
                ELSE
                    UPDATE topics
                        SET last_activity_time = created_time
                        WHERE topic_id = NEW.topic_id;
                END IF;
            END IF;

            RETURN NULL;
        END;
        $$ LANGUAGE plpgsql;
    """
    )
    op.execute("DROP TRIGGER update_topics_last_activity_time_update ON comments")
    op.execute(
        """
        CREATE TRIGGER update_topics_last_activity_time_update
            AFTER UPDATE ON comments
            FOR EACH ROW
            WHEN ((OLD.is_deleted IS DISTINCT FROM NEW.is_deleted)
                OR (OLD.is_removed IS DISTINCT FROM NEW.is_removed))
            EXECUTE PROCEDURE update_topics_last_activity_time();
    """
    )


def downgrade():
    # comment_notifications
    op.execute("DROP TRIGGER delete_comment_notifications_update ON comments")
    op.execute(
        """
        CREATE TRIGGER delete_comment_notifications_update
            AFTER UPDATE ON comments
            FOR EACH ROW
            WHEN (OLD.is_deleted = false AND NEW.is_deleted = true)
            EXECUTE PROCEDURE delete_comment_notifications();
    """
    )

    # comments
    op.execute(
        """
        CREATE OR REPLACE FUNCTION set_comment_deleted_time() RETURNS TRIGGER AS $$
        BEGIN
            NEW.deleted_time := current_timestamp;

            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """
    )
    op.execute("DROP TRIGGER delete_comment_set_deleted_time_update ON comments")
    op.execute(
        """
        CREATE TRIGGER delete_comment_set_deleted_time_update
            BEFORE UPDATE ON comments
            FOR EACH ROW
            WHEN (OLD.is_deleted = false AND NEW.is_deleted = true)
            EXECUTE PROCEDURE set_comment_deleted_time();
    """
    )

    op.execute("DROP TRIGGER remove_comment_set_removed_time_update ON comments")
    op.execute("DROP FUNCTION set_comment_removed_time()")

    # topic_visits
    op.execute("DROP TRIGGER update_topic_visits_num_comments_update ON comments")
    op.execute("DROP FUNCTION update_all_topic_visit_num_comments()")
    op.execute(
        """
        CREATE OR REPLACE FUNCTION decrement_all_topic_visit_num_comments() RETURNS TRIGGER AS $$
        BEGIN
            UPDATE topic_visits
                SET num_comments = num_comments - 1
                WHERE topic_id = OLD.topic_id AND
                    visit_time > OLD.created_time;

            RETURN NULL;
        END;
        $$ LANGUAGE plpgsql;
    """
    )
    op.execute(
        """
        CREATE TRIGGER update_topic_visits_num_comments_update
            AFTER UPDATE ON comments
            FOR EACH ROW
            WHEN (OLD.is_deleted = false AND NEW.is_deleted = true)
            EXECUTE PROCEDURE decrement_all_topic_visit_num_comments();
    """
    )

    # topics
    op.execute(
        """
        CREATE OR REPLACE FUNCTION update_topics_num_comments() RETURNS TRIGGER AS $$
        BEGIN
            IF (TG_OP = 'INSERT' AND NEW.is_deleted = FALSE) THEN
                UPDATE topics
                    SET num_comments = num_comments + 1
                    WHERE topic_id = NEW.topic_id;
            ELSIF (TG_OP = 'DELETE' AND OLD.is_deleted = FALSE) THEN
                UPDATE topics
                    SET num_comments = num_comments - 1
                    WHERE topic_id = OLD.topic_id;
            ELSIF (TG_OP = 'UPDATE') THEN
                IF (OLD.is_deleted = FALSE AND NEW.is_deleted = TRUE) THEN
                    UPDATE topics
                        SET num_comments = num_comments - 1
                        WHERE topic_id = NEW.topic_id;
                ELSIF (OLD.is_deleted = TRUE AND NEW.is_deleted = FALSE) THEN
                    UPDATE topics
                        SET num_comments = num_comments + 1
                        WHERE topic_id = NEW.topic_id;
                END IF;
            END IF;

            RETURN NULL;
        END;
        $$ LANGUAGE plpgsql;
    """
    )
    op.execute("DROP TRIGGER update_topics_num_comments_update ON comments")
    op.execute(
        """
        CREATE TRIGGER update_topics_num_comments_update
            AFTER UPDATE ON comments
            FOR EACH ROW
            WHEN (OLD.is_deleted IS DISTINCT FROM NEW.is_deleted)
            EXECUTE PROCEDURE update_topics_num_comments();
    """
    )

    op.execute(
        """
        CREATE OR REPLACE FUNCTION update_topics_last_activity_time() RETURNS TRIGGER AS $$
        DECLARE
            most_recent_comment RECORD;
        BEGIN
            IF (TG_OP = 'INSERT' AND NEW.is_deleted = FALSE) THEN
                UPDATE topics
                    SET last_activity_time = NOW()
                    WHERE topic_id = NEW.topic_id;
            ELSIF (TG_OP = 'UPDATE') THEN
                SELECT MAX(created_time) AS max_created_time
                INTO most_recent_comment
                FROM comments
                WHERE topic_id = NEW.topic_id AND
                    is_deleted = FALSE;

                IF most_recent_comment.max_created_time IS NOT NULL THEN
                    UPDATE topics
                        SET last_activity_time = most_recent_comment.max_created_time
                        WHERE topic_id = NEW.topic_id;
                ELSE
                    UPDATE topics
                        SET last_activity_time = created_time
                        WHERE topic_id = NEW.topic_id;
                END IF;
            END IF;

            RETURN NULL;
        END;
        $$ LANGUAGE plpgsql;
    """
    )
    op.execute("DROP TRIGGER update_topics_last_activity_time_update ON comments")
    op.execute(
        """
        CREATE TRIGGER update_topics_last_activity_time_update
            AFTER UPDATE ON comments
            FOR EACH ROW
            WHEN (OLD.is_deleted IS DISTINCT FROM NEW.is_deleted)
            EXECUTE PROCEDURE update_topics_last_activity_time();
    """
    )
