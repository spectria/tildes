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

# Set up the gunicorn_reloader service, which reloads gunicorn whenever certain files
# are changed (such as static files, to update the cache-busting strings)
/etc/systemd/system/gunicorn_reloader.service:
  file.managed:
    - source: salt://gunicorn/gunicorn_reloader.service
    - user: root
    - group: root
    - mode: 644
    - require_in:
      - service: gunicorn_reloader.path

/etc/systemd/system/gunicorn_reloader.path:
  file.managed:
    - source: salt://gunicorn/gunicorn_reloader.path
    - user: root
    - group: root
    - mode: 644
    - require_in:
      - service: gunicorn_reloader.path

gunicorn_reloader.path:
  service.running:
    - enable: True
