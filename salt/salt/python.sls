{% from 'common.jinja2' import app_dir, app_username, bin_dir, python_version, venv_dir %}

deadsnakes:
  pkgrepo.managed:
    - ppa: deadsnakes/ppa
  pkg.installed:
    - name: python{{ python_version }}
    - refresh: True

/opt/venvs:
  file.directory:
    - user: {{ app_username }}
    - group: {{ app_username }}
    - dir_mode: 755

delete-obsolete-venv:
  file.absent:
    - name: {{ venv_dir }}
    - unless: {{ bin_dir }}/python --version | grep {{ python_version }}

# Salt seems to use the deprecated pyvenv script, manual for now
venv-setup:
  pkg.installed:
    - name: python{{ python_version }}-venv
  cmd.run:
    - name: python{{ python_version }} -m venv {{ venv_dir }}
    - creates: {{ venv_dir }}
    - runas: {{ app_username }}
    - require:
      - pkg: python{{ python_version }}-venv

# Packages needed to be able to compile psycopg2 (while installing requirements.txt)
psycopg2-deps:
  pkg.installed:
    - pkgs:
      - gcc
      - libpq-dev
      - python{{ python_version }}-dev

pip-installs:
  pip.installed:
    {% if grains['id'] == 'dev' %}
    - requirements: {{ app_dir }}/requirements-dev.txt
    {% else %}
    - requirements: {{ app_dir }}/requirements.txt
    {% endif %}
    - user: {{ app_username }}
    - bin_env: {{ venv_dir }}
  require:
    - cmd: venv-setup
    - pkg: psycopg2-deps

self-install:
  pip.installed:
    - bin_env: {{ venv_dir }}
    - editable:
      - {{ app_dir }}
    - require:
      - cmd: venv-setup
    - unless: ls {{ venv_dir }}/lib/python{{ python_version }}/site-packages/tildes.egg-link
