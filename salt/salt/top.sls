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
    - redis.breached-passwords
    - redis.modules.rebloom
    - redis.modules.redis-cell
    - rabbitmq
    - scripts
    - cmark-gfm
    - prometheus.exporters.node_exporter
    - prometheus.exporters.postgres_exporter
    - prometheus.exporters.rabbitmq_exporter
    - prometheus.exporters.redis_exporter
    - consumers
    - tildes-wiki
    - boussole
    - webassets
    - cronjobs
    - final-setup  # keep this state file last
  'dev':
    - postgresql.test-db
    - self-signed-cert
    - development
    - prometheus
    - nodejs
  'prod':
    - nginx.shortener-config
    - nginx.static-sites-config
    - prod-config
  'monitoring':
    - nginx
    - self-signed-cert
    - postgresql
    - redis
    - sentry
    - grafana
    - prometheus
