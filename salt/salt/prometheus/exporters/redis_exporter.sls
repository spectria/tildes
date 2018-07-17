# Download/extract and set up the redis exporter
include:
  - prometheus.user

unpack-redis-exporter:
  archive.extracted:
    - name: /opt/prometheus_redis_exporter
    - source:
      - salt://prometheus/exporters/redis_exporter-v0.10.7.linux-amd64.tar.gz
      - https://github.com/oliver006/redis_exporter/releases/download/v0.10.7/redis_exporter-v0.10.7.linux-amd64.tar.gz
    - source_hash: sha256=b9b48f321a201f3b424f1710d2cac1bca03272d67001812d8b2fb6305099fb09
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
