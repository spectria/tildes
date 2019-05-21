{% from 'common.jinja2' import app_username %}

/etc/systemd/system/gunicorn.service:
  file.managed:
    - source: salt://gunicorn/gunicorn.service.jinja2
    - template: jinja
    - user: root
    - group: root
    - mode: 644
    - require_in:
      - service: gunicorn.socket

/etc/systemd/system/gunicorn.socket:
  file.managed:
    - source: salt://gunicorn/gunicorn.socket.jinja2
    - template: jinja
    - user: root
    - group: root
    - mode: 644
    - require_in:
      - service: gunicorn.socket

/usr/lib/tmpfiles.d/gunicorn.conf:
  file.managed:
    - source: salt://gunicorn/gunicorn.conf.jinja2
    - template: jinja
    - user: root
    - group: root
    - mode: 644
    - require_in:
      - service: gunicorn.socket

gunicorn.socket:
  service.running:
    - enable: True
