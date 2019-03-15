"""Send rabbitmq message on link edit

Revision ID: 4ebc3ca32b48
Revises: 24014adda7c3
Create Date: 2019-03-15 00:59:57.713065

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "4ebc3ca32b48"
down_revision = "24014adda7c3"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        """
        CREATE TRIGGER send_rabbitmq_message_for_topic_link_edit
            AFTER UPDATE ON topics
            FOR EACH ROW
            WHEN (OLD.link IS DISTINCT FROM NEW.link)
            EXECUTE PROCEDURE send_rabbitmq_message_for_topic('link_edited');
    """
    )


def downgrade():
    op.execute("DROP TRIGGER send_rabbitmq_message_for_topic_link_edit ON topics")
