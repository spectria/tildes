# Download/extract and set up the blackbox exporter
include:
  - prometheus.user

unpack-blackbox-exporter:
  archive.extracted:
    - name: /opt/prometheus_blackbox_exporter
    - source:
      - salt://prometheus/exporters/blackbox_exporter-0.16.0.linux-amd64.tar.gz
      - https://github.com/prometheus/blackbox_exporter/releases/download/v0.16.0/blackbox_exporter-0.16.0.linux-amd64.tar.gz
    - source_hash: sha256=52d3444a518ea01f220e08eaa53eb717ef54da6724760c925ab41285d0d5a7bd
    - if_missing: /opt/prometheus_blackbox_exporter
    - user: prometheus
    - group: prometheus
    - options: --strip-components=1
    - enforce_toplevel: False

/opt/prometheus_blackbox_exporter/blackbox.yml:
  file.managed:
    - source: salt://prometheus/exporters/blackbox.yml
    - user: prometheus
    - group: prometheus
    - mode: 644

/etc/systemd/system/prometheus_blackbox_exporter.service:
  file.managed:
    - source: salt://prometheus/exporters/prometheus_blackbox_exporter.service
    - user: root
    - group: root
    - mode: 644

prometheus-blackbox-exporter-service:
  service.running:
    - name: prometheus_blackbox_exporter
    - enable: True
