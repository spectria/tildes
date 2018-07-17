install-pgbouncer:
  pkg.installed:
    - name: pgbouncer

/etc/pgbouncer/pgbouncer.ini:
  file.managed:
    - source: salt://postgresql/pgbouncer.ini.jinja2
    - template: jinja
    - user: postgres
    - group: postgres
    - mode: 640

/etc/pgbouncer/userlist.txt:
  file.managed:
    - contents: '"tildes" ""'
    - user: postgres
    - group: postgres
    - mode: 640

pgbouncer.service:
  service.running:
    - enable: True
    - reload: True
    - watch:
      - file: /etc/pgbouncer/pgbouncer.ini
