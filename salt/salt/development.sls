{% from 'common.jinja2' import app_username, bin_dir %}

{% set profile_dir = '/home/' + app_username + '/.ipython/profile_default' %}

ipython-profile:
  cmd.run:
    - name: {{ bin_dir }}/ipython profile create
    - runas: {{ app_username }}
    - creates: {{ profile_dir }}
  file.managed:
    - name: {{ profile_dir }}/ipython_config.py
    - contents:
      - c.InteractiveShellApp.extensions = ['autoreload']
      - c.InteractiveShellApp.exec_lines = ['%autoreload 2']
  require:
    - pip: pip-installs

automatic-activate:
  file.append:
    - name: '/home/{{ app_username }}/.bashrc'
    - text: 'source activate'
