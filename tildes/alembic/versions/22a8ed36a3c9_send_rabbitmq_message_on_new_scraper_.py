"""Send rabbitmq message on new scraper result

Revision ID: 22a8ed36a3c9
Revises: 8e54f422541c
Create Date: 2018-09-30 21:14:29.265490

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "22a8ed36a3c9"
down_revision = "8e54f422541c"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        """
        CREATE OR REPLACE FUNCTION send_rabbitmq_message_for_scraper_result() RETURNS TRIGGER AS $$
        DECLARE
            affected_row RECORD;
            payload TEXT;
        BEGIN
            IF (TG_OP = 'INSERT' OR TG_OP = 'UPDATE') THEN
                affected_row := NEW;
            ELSIF (TG_OP = 'DELETE') THEN
                affected_row := OLD;
            END IF;

            payload := json_build_object('result_id', affected_row.result_id);

            PERFORM send_rabbitmq_message('scraper_result.' || TG_ARGV[0], payload);

            RETURN NULL;
        END;
        $$ LANGUAGE plpgsql;
    """
    )

    op.execute(
        """
        CREATE TRIGGER send_rabbitmq_message_for_scraper_result_insert
            AFTER INSERT ON scraper_results
            FOR EACH ROW
            EXECUTE PROCEDURE send_rabbitmq_message_for_scraper_result('created');
    """
    )


def downgrade():
    op.execute(
        "DROP TRIGGER send_rabbitmq_message_for_scraper_result_insert ON scraper_results"
    )

    op.execute("DROP FUNCTION send_rabbitmq_message_for_scraper_result()")
