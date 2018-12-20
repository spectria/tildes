base:
  'dev or prod':
    - gunicorn
    - nginx
    - nginx.site-config
    - postgresql
    - postgresql.site-db
    - postgresql.pgbouncer
    - python
    - redis
    - redis.modules.rebloom
    - redis.modules.redis-cell
    - rabbitmq
    - scripts
    - cmark-gfm
    - prometheus.exporters.node_exporter
    - prometheus.exporters.postgres_exporter
    - prometheus.exporters.redis_exporter
    - consumers
    - site-icons-spriter
    - boussole
    - webassets
    - cronjobs
    - final-setup  # keep this state file last
  'dev':
    - postgresql.test-db
    - self-signed-cert
    - development
    - prometheus
  'prod':
    - nginx.shortener-config
    - nginx.static-sites-config
    - raven
    - prod-config
  'monitoring':
    - nginx
    - self-signed-cert
    - postgresql
    - redis
    - sentry
    - grafana
    - prometheus
