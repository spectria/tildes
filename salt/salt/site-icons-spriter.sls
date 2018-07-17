{% from 'common.jinja2' import app_dir, app_username, python_version %}

{% set site_icons_venv_dir = '/opt/venvs/site-icons-spriter' %}
{% set site_icons_data_dir = '/var/lib/site-icons-spriter' %}

# Salt seems to use the deprecated pyvenv script, manual for now
site-icons-venv-setup:
  cmd.run:
    - name: /usr/local/pyenv/versions/{{ python_version }}/bin/python -m venv {{ site_icons_venv_dir }}
    - creates: {{ site_icons_venv_dir }}
    - require:
      - pkg: python3-venv
      - pyenv: {{ python_version }}

site-icons-pip-installs:
  cmd.run:
    - name: {{ site_icons_venv_dir }}/bin/pip install glue
    - unless: ls {{ site_icons_venv_dir }}/lib/python3.6/site-packages/glue

site-icons-output-placeholder:
  file.managed:
    - name: {{ site_icons_data_dir }}/output/site-icons.css
    - contents: ''
    - allow_empty: True
    - makedirs: True
    - user: {{ app_username }}
    - group: {{ app_username }}
    - unless: ls {{ site_icons_data_dir }}/output/site-icons.css

site-icons-input-folder:
  file.directory:
    - name: {{ site_icons_data_dir }}/site-icons
    - user: {{ app_username }}
    - group: {{ app_username }}

/usr/local/bin/generate-site-icons:
  file.managed:
    - source: salt://scripts/generate-site-icons.sh.jinja2
    - template: jinja
    - user: root
    - group: root
    - mode: 755
