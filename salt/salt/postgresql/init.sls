postgresql:
  pkgrepo.managed:
    - name: deb http://apt.postgresql.org/pub/repos/apt/ xenial-pgdg main
    - dist: xenial-pgdg
    - file: /etc/apt/sources.list.d/psql.list
    - key_url: https://www.postgresql.org/media/keys/ACCC4CF8.asc
    - require_in:
      - pkg: postgresql
  pkg.installed:
    - name: postgresql-{{ pillar['postgresql_version'] }}
    - refresh: True
  service.running:
    - require:
      - pkg: postgresql
    - reload: True
    - watch:
      - file: /etc/postgresql/{{ pillar['postgresql_version'] }}/main/*.conf

set-lock-timeout:
  file.replace:
    - name: /etc/postgresql/{{ pillar['postgresql_version'] }}/main/postgresql.conf
    - pattern: '^#?lock_timeout = (?!5000).*$'
    - repl: 'lock_timeout = 5000'

set-statement-timeout:
  file.replace:
    - name: /etc/postgresql/{{ pillar['postgresql_version'] }}/main/postgresql.conf
    - pattern: '^#?statement_timeout = (?!5000).*$'
    - repl: 'statement_timeout = 5000'

set-idle-in-transaction-timeout:
  file.replace:
    - name: /etc/postgresql/{{ pillar['postgresql_version'] }}/main/postgresql.conf
    - pattern: '^#?idle_in_transaction_session_timeout = (?!600000).*$'
    - repl: 'idle_in_transaction_session_timeout = 600000'

set-timezone:
  file.replace:
    - name: /etc/postgresql/{{ pillar['postgresql_version'] }}/main/postgresql.conf
    - pattern: '^#?timezone = (?!''UTC'').*$'
    - repl: 'timezone = ''UTC'''

enable-pg-stat-statements:
  file.replace:
    - name: /etc/postgresql/{{ pillar['postgresql_version'] }}/main/postgresql.conf
    - pattern: '^#?shared_preload_libraries = .*$'
    - repl: "shared_preload_libraries = 'pg_stat_statements'"
    - watch_in:
      - module: enable-pg-stat-statements
  module.wait:
    - service.restart:
      - name: postgresql.service

/etc/postgresql/{{ pillar['postgresql_version'] }}/main/pg_hba.conf:
  file.managed:
    - source: salt://postgresql/pg_hba.conf.jinja2
    - template: jinja
    - user: postgres
    - group: postgres
    - mode: 640
  require:
    - service: postgresql
