{% from 'common.jinja2' import app_dir, python_version %}

{% set boussole_venv_dir = '/opt/venvs/boussole' %}

# Salt seems to use the deprecated pyvenv script, manual for now
boussole-venv-setup:
  cmd.run:
    - name: python{{ python_version }} -m venv {{ boussole_venv_dir }}
    - creates: {{ boussole_venv_dir }}
    - require:
      - pkg: python{{ python_version }}-venv

boussole-pip-installs:
  cmd.run:
    - name: {{ boussole_venv_dir }}/bin/pip install boussole
    - unless: ls {{ boussole_venv_dir }}/lib/python{{ python_version }}/site-packages/boussole

/etc/systemd/system/boussole.service:
  file.managed:
    - source: salt://boussole.service.jinja2
    - template: jinja
    - user: root
    - group: root
    - mode: 644
    - require_in:
      - service: boussole.service

boussole.service:
  service.running:
    - enable: True
    - require:
      - pip: pip-installs

create-css-directory:
  file.directory:
    - name: {{ app_dir }}/static/css

initial-boussole-run:
  cmd.run:
    - name: {{ boussole_venv_dir }}/bin/boussole compile --backend=yaml --config=boussole.yaml
    - cwd: {{ app_dir }}
    - env:
      - LC_ALL: C.UTF-8
      - LANG: C.UTF-8
    - require:
      - file: create-css-directory
    - unless: ls {{ app_dir }}/static/css/*.css
