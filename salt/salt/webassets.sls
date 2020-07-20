{% from 'common.jinja2' import app_dir, app_username %}

# webassets will crash the site unless this file exists, make sure it's always there
{{ app_dir }}/static/css/site-icons.css:
  file.managed:
    - user: {{ app_username }}
    - group: {{ app_username }}
    - create: True
    - replace: False

/etc/systemd/system/webassets.service:
  file.managed:
    - source: salt://webassets.service.jinja2
    - template: jinja
    - user: root
    - group: root
    - mode: 644
    - require_in:
      - service: webassets.service

webassets.service:
  service.running:
    - enable: True
    - require:
      - pip: pip-installs
