# Download/extract and set up the redis exporter
include:
  - prometheus.user

unpack-redis-exporter:
  archive.extracted:
    - name: /opt/prometheus_redis_exporter
    - source:
      - salt://prometheus/exporters/redis_exporter-v0.26.0.linux-amd64.tar.gz
      - https://github.com/oliver006/redis_exporter/releases/download/v0.26.0/redis_exporter-v0.26.0.linux-amd64.tar.gz
    - source_hash: sha256=39354c57b9d02b455c584baf46a2df6ed3d1ac190c88e3ec0fa0c23b49ccc2bb
    - if_missing: /opt/prometheus_redis_exporter
    - user: prometheus
    - group: prometheus
    - enforce_toplevel: False

/etc/systemd/system/prometheus_redis_exporter.service:
  file.managed:
    - source: salt://prometheus/exporters/prometheus_redis_exporter.service
    - user: root
    - group: root
    - mode: 644

prometheus-redis-exporter-service:
  service.running:
    - name: prometheus_redis_exporter
    - enable: True
