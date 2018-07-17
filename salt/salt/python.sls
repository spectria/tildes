{% from 'common.jinja2' import app_dir, bin_dir, python_version, venv_dir %}

pyenv-deps:
  pkg.installed:
    - pkgs:
      - build-essential
      - curl
      - libbz2-dev
      - libncurses5-dev
      - libncursesw5-dev
      - libreadline-dev
      - libsqlite3-dev
      - libssl-dev
      - llvm
      - make
      - wget
      - xz-utils
      - zlib1g-dev

python-3.6:
  pyenv.installed:
    - name: {{ python_version }}
    - default: True
    - require:
      - pkg: pyenv-deps

delete-obsolete-venv:
  file.absent:
    - name: {{ venv_dir }}
    - unless: {{ bin_dir }}/python --version | grep {{ python_version }}

# Salt seems to use the deprecated pyvenv script, manual for now
venv-setup:
  pkg.installed:
    - name: python3-venv
  cmd.run:
    - name: /usr/local/pyenv/versions/{{ python_version }}/bin/python -m venv {{ venv_dir }}
    - creates: {{ venv_dir }}
    - require:
      - pkg: python3-venv
      - pyenv: {{ python_version }}

pip-installs:
  pip.installed:
    - requirements: {{ app_dir }}/requirements.txt
    - bin_env: {{ venv_dir }}
  require:
    - cmd: venv-setup
    - pkg: pip-deps

self-install:
  pip.installed:
    - bin_env: {{ venv_dir }}
    - editable:
      - {{ app_dir }}
    - require:
      - cmd: venv-setup
    - unless: ls {{ venv_dir }}/lib/python3.6/site-packages/tildes.egg-link
