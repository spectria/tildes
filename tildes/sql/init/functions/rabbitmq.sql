-- Copyright (c) 2018 Tildes contributors <code@tildes.net>
-- SPDX-License-Identifier: AGPL-3.0-or-later

CREATE OR REPLACE FUNCTION send_rabbitmq_message(routing_key TEXT, message TEXT) RETURNS VOID AS $$
    SELECT pg_notify('pgsql_events', routing_key || '|' || message);
$$ STABLE LANGUAGE SQL;
