# Download and set up the postgres exporter
include:
  - prometheus.user

postgres-exporter:
  file.managed:
    - name: /opt/prometheus_postgres_exporter/postgres_exporter
    - source:
      - salt://prometheus/exporters/postgres_exporter
      - https://github.com/wrouesnel/postgres_exporter/releases/download/v0.3.0/postgres_exporter
    - source_hash: sha256=44654860e3122acf183e8cad504bddc3bf9dd717910cddc99b589a3463d2ec6f
    - user: postgres
    - group: postgres
    - mode: 774
    - makedirs: True
    - unless: ls /opt/prometheus_postgres_exporter/postgres_exporter

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
