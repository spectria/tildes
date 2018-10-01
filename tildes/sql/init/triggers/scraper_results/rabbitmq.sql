-- Copyright (c) 2018 Tildes contributors <code@tildes.net>
-- SPDX-License-Identifier: AGPL-3.0-or-later

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


CREATE TRIGGER send_rabbitmq_message_for_scraper_result_insert
    AFTER INSERT ON scraper_results
    FOR EACH ROW
    EXECUTE PROCEDURE send_rabbitmq_message_for_scraper_result('created');
