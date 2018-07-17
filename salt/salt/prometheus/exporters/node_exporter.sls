# Download/extract and set up the node exporter (hardware/OS metrics)
include:
  - prometheus.user

unpack-node-exporter:
  archive.extracted:
    - name: /opt/prometheus_node_exporter
    - source:
      - salt://prometheus/exporters/node_exporter-0.13.0.linux-amd64.tar.gz
      - https://github.com/prometheus/node_exporter/releases/download/v0.13.0/node_exporter-0.13.0.linux-amd64.tar.gz
    - source_hash: sha256=2de5d1e51330c41588ed4c88bc531a3d2dccf6b4d7b99d5782d95cff27a3c049
    - if_missing: /opt/prometheus_node_exporter
    - user: prometheus
    - group: prometheus
    - options: --strip-components=1
    - enforce_toplevel: False

/etc/systemd/system/prometheus_node_exporter.service:
  file.managed:
    - source: salt://prometheus/exporters/prometheus_node_exporter.service
    - user: root
    - group: root
    - mode: 644

prometheus-node-exporter-service:
  service.running:
    - name: prometheus_node_exporter
    - enable: True
