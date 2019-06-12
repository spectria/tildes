"""Add "interesting activity" topic sorting

Revision ID: cddd7d7ed0ea
Revises: a2fda5d4e058
Create Date: 2019-06-10 20:20:58.652760

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "cddd7d7ed0ea"
down_revision = "a2fda5d4e058"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "topics",
        sa.Column(
            "last_interesting_activity_time",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
    )
    op.create_index(
        op.f("ix_topics_last_interesting_activity_time"),
        "topics",
        ["last_interesting_activity_time"],
        unique=False,
    )

    op.execute("UPDATE topics SET last_interesting_activity_time = last_activity_time")

    op.execute(
        """
        CREATE TRIGGER send_rabbitmq_message_for_comment_delete
            AFTER UPDATE ON comments
            FOR EACH ROW
            WHEN (OLD.is_deleted = false AND NEW.is_deleted = true)
            EXECUTE PROCEDURE send_rabbitmq_message_for_comment('deleted');


        CREATE TRIGGER send_rabbitmq_message_for_comment_undelete
            AFTER UPDATE ON comments
            FOR EACH ROW
            WHEN (OLD.is_deleted = true AND NEW.is_deleted = false)
            EXECUTE PROCEDURE send_rabbitmq_message_for_comment('undeleted');


        CREATE TRIGGER send_rabbitmq_message_for_comment_remove
            AFTER UPDATE ON comments
            FOR EACH ROW
            WHEN (OLD.is_removed = false AND NEW.is_removed = true)
            EXECUTE PROCEDURE send_rabbitmq_message_for_comment('removed');


        CREATE TRIGGER send_rabbitmq_message_for_comment_unremove
            AFTER UPDATE ON comments
            FOR EACH ROW
            WHEN (OLD.is_removed = true AND NEW.is_removed = false)
            EXECUTE PROCEDURE send_rabbitmq_message_for_comment('unremoved');


        CREATE TRIGGER send_rabbitmq_message_for_comment_label_delete
            AFTER DELETE ON comment_labels
            FOR EACH ROW
            EXECUTE PROCEDURE send_rabbitmq_message_for_comment_label('deleted');
    """
    )

    # manually commit before disabling the transaction for ALTER TYPE
    op.execute("COMMIT")

    # ALTER TYPE doesn't work from inside a transaction, disable it
    connection = None
    if not op.get_context().as_sql:
        connection = op.get_bind()
        connection.execution_options(isolation_level="AUTOCOMMIT")

    op.execute("ALTER TYPE topicsortoption ADD VALUE IF NOT EXISTS 'ALL_ACTIVITY'")

    # re-activate the transaction for any future migrations
    if connection is not None:
        connection.execution_options(isolation_level="READ_COMMITTED")


def downgrade():
    op.execute(
        "DROP TRIGGER send_rabbitmq_message_for_comment_label_delete ON comment_labels"
    )
    op.execute("DROP TRIGGER send_rabbitmq_message_for_comment_unremove ON comments")
    op.execute("DROP TRIGGER send_rabbitmq_message_for_comment_remove ON comments")
    op.execute("DROP TRIGGER send_rabbitmq_message_for_comment_undelete ON comments")
    op.execute("DROP TRIGGER send_rabbitmq_message_for_comment_delete ON comments")

    op.drop_index(op.f("ix_topics_last_interesting_activity_time"), table_name="topics")
    op.drop_column("topics", "last_interesting_activity_time")
