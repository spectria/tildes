include:
  - prometheus.user

unpack-prometheus:
  archive.extracted:
    - name: /opt/prometheus
    - source:
      - salt://prometheus/prometheus-2.0.0.linux-amd64.tar.gz
      - https://github.com/prometheus/prometheus/releases/download/v2.0.0/prometheus-2.0.0.linux-amd64.tar.gz
    - source_hash: sha256=e12917b25b32980daee0e9cf879d9ec197e2893924bd1574604eb0f550034d46
    - if_missing: /opt/prometheus
    - user: prometheus
    - group: prometheus
    - options: --strip-components=1
    - enforce_toplevel: False

/etc/systemd/system/prometheus.service:
  file.managed:
    - source: salt://prometheus/prometheus.service
    - user: root
    - group: root
    - mode: 644

prometheus-service:
  service.running:
    - name: prometheus
    - enable: True
    - watch:
      - file: /opt/prometheus/prometheus.yml


/opt/prometheus/prometheus.yml:
  file.managed:
    - source: salt://prometheus/prometheus.yml.jinja2
    - template: jinja
    - user: prometheus
    - group: prometheus
    - mode: 664

{# Set up nginx to reverse-proxy to prometheus in production #}
{% if grains['id'] == 'prod' %}
/etc/nginx/sites-available/prometheus.conf:
  file.managed:
    - source: salt://prometheus/prometheus.conf.jinja2
    - template: jinja
    - user: root
    - group: root
    - mode: 644
    - makedirs: True

/etc/nginx/sites-enabled/prometheus.conf:
  file.symlink:
    - target: /etc/nginx/sites-available/prometheus.conf
    - makedirs: True
    - user: root
    - group: root
    - mode: 644
{% endif %}
