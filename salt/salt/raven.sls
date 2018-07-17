{% from 'common.jinja2' import app_dir, venv_dir %}

raven-pip-install:
  pip.installed:
    - name: raven
    - bin_env: {{ venv_dir }}
