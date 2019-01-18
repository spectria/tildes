{% from 'sentry/common.jinja2' import sentry_bin_dir, sentry_cfg_dir, sentry_venv_dir %}

sentry-user:
  group.present:
    - name: sentry
  user.present:
    - name: sentry
    - groups: [sentry]

build-deps:
  pkg.installed:
    - pkgs:
      - python-setuptools
      - python-dev
      - python-pip
      - python-virtualenv
      - libxslt1-dev
      - gcc
      - libffi-dev
      - libjpeg-dev
      - libxml2-dev
      - libxslt-dev
      - libyaml-dev
      - libpq-dev
      - zlib1g-dev
      - postgresql-server-dev-{{ pillar['postgresql_version'] }}

{{ sentry_venv_dir }}:
  virtualenv.managed:
    - system_site_packages: False

pip-install:
  pip.installed:
    - name: sentry
    - bin_env: {{ sentry_venv_dir }}

pip-install-plugins:
  pip.installed:
    - name: sentry-plugins
    - bin_env: {{ sentry_venv_dir }}

init-sentry:
  cmd.run:
    - name: {{ sentry_bin_dir }}/sentry init {{ sentry_cfg_dir }}
    - creates: {{ sentry_cfg_dir }}

postgres-setup:
  postgres_user.present:
    - name: sentry
  postgres_database.present:
    - name: sentry
    - owner: sentry
  # sentry migrations should add this, but it fails due to not being superuser
  postgres_extension.present:
    - name: citext
    - maintenance_db: sentry

{{ sentry_cfg_dir }}/sentry.conf.py:
  file.managed:
    - source: salt://sentry/sentry.conf.py

{{ sentry_cfg_dir }}/config.yml:
  file.managed:
    - source: salt://sentry/config.yml.jinja2
    - template: jinja

update-pg_hba:
  file.accumulated:
    - name: pg_hba_lines
    - filename: /etc/postgresql/{{ pillar['postgresql_version'] }}/main/pg_hba.conf
    - text: 'host    sameuser        sentry      127.0.0.1/32   trust'
    - require_in:
      - file: /etc/postgresql/{{ pillar['postgresql_version'] }}/main/pg_hba.conf

create-sentry-db:
  cmd.run:
    - name: {{ sentry_bin_dir }}/sentry upgrade --noinput
    - env:
      - SENTRY_CONF: '{{ sentry_cfg_dir }}'
    - onchanges:
      - cmd: init-sentry

create-sentry-user:
  cmd.run:
    - name: {{ sentry_bin_dir }}/sentry createuser --no-input --email {{ pillar['sentry_email'] }} --password {{ pillar['sentry_password'] }}
    - env:
      - SENTRY_CONF: '{{ sentry_cfg_dir }}'
    - onchanges:
      - cmd: init-sentry

/etc/systemd/system/sentry-web.service:
  file.managed:
    - source: salt://sentry/sentry-web.service.jinja2
    - template: jinja
    - user: root
    - group: root
    - mode: 644

/etc/systemd/system/sentry-worker.service:
  file.managed:
    - source: salt://sentry/sentry-worker.service.jinja2
    - template: jinja
    - user: root
    - group: root
    - mode: 644

/etc/systemd/system/sentry-cron.service:
  file.managed:
  - source: salt://sentry/sentry-cron.service.jinja2
  - template: jinja
  - user: root
  - group: root
  - mode: 644

sentry-web:
  service.running:
    - enable: True

sentry-worker:
  service.running:
    - enable: True

sentry-cron:
  service.running:
    - enable: True

sentry-cleanup:
  cron.present:
    - name: {{ sentry_bin_dir }}/sentry cleanup --days=30
    - hour: 4
    - minute: 0

/etc/nginx/sites-available/sentry.conf:
  file.managed:
    - source: salt://sentry/sentry.conf.jinja2
    - template: jinja
    - user: root
    - group: root
    - mode: 644
    - makedirs: True

/etc/nginx/sites-enabled/sentry.conf:
  file.symlink:
    - target: /etc/nginx/sites-available/sentry.conf
    - makedirs: True
    - user: root
    - group: root
    - mode: 644
