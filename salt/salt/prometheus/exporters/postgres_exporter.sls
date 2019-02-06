# Download and set up the postgres exporter
include:
  - prometheus.user

unpack-postgres-exporter:
  archive.extracted:
    - name: /opt/prometheus_postgres_exporter
    - source:
      - salt://prometheus/exporters/postgres_exporter_v0.4.7_linux-amd64.tar.gz
      - https://github.com/wrouesnel/postgres_exporter/releases/download/v0.4.7/postgres_exporter_v0.4.7_linux-amd64.tar.gz
    - source_hash: sha256=c34d61bb4deba8efae06fd3c9979b96dae3f3c757698ce3384c80fff586c667b
    - if_missing: /opt/prometheus_postgres_exporter
    - user: postgres
    - group: postgres
    - mode: 774
    - options: --strip-components=1
    - enforce_toplevel: False

/opt/prometheus_postgres_exporter/queries.yaml:
  file.managed:
    - source: salt://prometheus/exporters/queries.yaml
    - user: postgres
    - group: postgres
    - mode: 644

/etc/systemd/system/prometheus_postgres_exporter.service:
  file.managed:
    - source: salt://prometheus/exporters/prometheus_postgres_exporter.service
    - user: root
    - group: root
    - mode: 644

prometheus-postgres-exporter-service:
  service.running:
    - name: prometheus_postgres_exporter
    - enable: True
