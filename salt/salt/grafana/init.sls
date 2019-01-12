grafana:
  pkgrepo.managed:
    - name: deb https://packages.grafana.com/oss/deb stable main
    - dist: stable
    - file: /etc/apt/sources.list.d/grafana.list
    - key_url: https://packages.grafana.com/gpg.key
    - require_in:
      - pkg: grafana
  pkg.installed:
    - name: grafana
    - refresh: True
  # note: this file must be set up before the server is started for the first
  # time, otherwise the admin password will not be set correctly
  file.managed:
    - name: /etc/grafana/grafana.ini
    - source: salt://grafana/grafana.ini.jinja2
    - template: jinja
    - user: root
    - group: grafana
    - mode: 640
  service.running:
    - name: grafana-server
    - enable: True
    - require:
      - pkg: grafana
      - file: /etc/grafana/grafana.ini
    - watch:
      - file: /etc/grafana/grafana.ini
  http.query:
    - name: http://localhost:3000/api/datasources
    - method: POST
    - username: admin
    - password: {{ pillar['grafana_admin_password'] }}
    - data: |
        {"name": "Prometheus",
        "type": "prometheus",
        "url": "http://localhost:9090",
        "access": "proxy",
        "isDefault": true}
    - header_list:
      - 'Content-Type: application/json'
    - status: 200
    - unless:
      - curl -f http://admin:{{ pillar['grafana_admin_password'] }}@localhost:3000/api/datasources/name/Prometheus

/etc/nginx/sites-available/grafana.conf:
  file.managed:
    - source: salt://grafana/grafana.conf.jinja2
    - template: jinja
    - user: root
    - group: root
    - mode: 644
    - makedirs: True

/etc/nginx/sites-enabled/grafana.conf:
  file.symlink:
    - target: /etc/nginx/sites-available/grafana.conf
    - makedirs: True
    - user: root
    - group: root
    - mode: 644
