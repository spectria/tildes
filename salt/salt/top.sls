base:
  'dev or prod':
    - general-config
    - gunicorn
    - nginx
    - nginx.site-config
    - postgresql
    - postgresql.site-db
    - postgresql.pgbouncer
    - python
    - redis
    - redis.modules.redis-cell
    - postgresql-redis-bridge
    - scripts
    - cmark-gfm
    - prometheus.exporters.node_exporter
    - prometheus.exporters.postgres_exporter
    - prometheus.exporters.redis_exporter
    - consumers
    - tildes-wiki
    - boussole
    - webassets
    - pts-lbsearch
    - cronjobs
    - final-setup  # keep this state file last
  'dev':
    - postgresql.test-db
    - self-signed-cert
    - development
    - prometheus
    - nodejs
    - java
  'prod':
    - nginx.shortener-config
    - nginx.static-sites-config
    - postgresql.prod-config
    - prod-config
  'monitoring':
    - nginx
    - self-signed-cert
    - postgresql
    - redis
    - sentry
    - grafana
    - prometheus
    - prometheus.exporters.blackbox_exporter
