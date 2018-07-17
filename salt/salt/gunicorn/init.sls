gunicorn:
  group.present:
    - name: gunicorn
  user.present:
    - name: gunicorn
    - groups: [gunicorn]
    - createhome: False

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
    - source: salt://gunicorn/gunicorn.socket
    - user: root
    - group: root
    - mode: 644
    - require_in:
      - service: gunicorn.socket

/usr/lib/tmpfiles.d/gunicorn.conf:
  file.managed:
    - source: salt://gunicorn/gunicorn.conf
    - user: root
    - group: root
    - mode: 644
    - require_in:
      - service: gunicorn.socket

gunicorn.socket:
  service.running:
    - enable: True
    - require:
      - user: gunicorn
