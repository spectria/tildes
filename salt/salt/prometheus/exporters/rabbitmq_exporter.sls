# Download/extract and set up the rabbitmq exporter
include:
  - prometheus.user

unpack-rabbitmq-exporter:
  archive.extracted:
    - name: /opt/prometheus_rabbitmq_exporter
    - source:
      - salt://prometheus/exporters/rabbitmq_exporter-1.0.0-WIP.linux-amd64.tar.gz
      - https://github.com/kbudde/rabbitmq_exporter/releases/download/v1.0-wip1/rabbitmq_exporter-1.0.0-WIP.linux-amd64.tar.gz
    - source_hash: sha256=d478dcf72d8a5175a4f3ea6b8e0356f64e2fcdb7b65bb5bfc0bd161d896abc4a
    - if_missing: /opt/prometheus_rabbitmq_exporter
    - user: prometheus
    - group: prometheus
    - options: --strip-components=1
    - enforce_toplevel: False

/etc/systemd/system/prometheus_rabbitmq_exporter.service:
  file.managed:
    - source: salt://prometheus/exporters/prometheus_rabbitmq_exporter.service
    - user: root
    - group: root
    - mode: 644

prometheus-rabbitmq-exporter-service:
  service.running:
    - name: prometheus_rabbitmq_exporter
    - enable: True
