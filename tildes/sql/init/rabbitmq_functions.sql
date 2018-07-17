CREATE OR REPLACE FUNCTION send_rabbitmq_message(routing_key TEXT, message TEXT) RETURNS VOID AS $$
    SELECT pg_notify('pgsql_events', routing_key || '|' || message);
$$ STABLE LANGUAGE SQL;
