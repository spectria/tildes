{% from 'common.jinja2' import app_dir, bin_dir %}

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
    - name: {{ bin_dir }}/boussole compile --backend=yaml --config=boussole.yaml
    - cwd: {{ app_dir }}
    - env:
      - LC_ALL: C.UTF-8
      - LANG: C.UTF-8
    - require:
      - file: create-css-directory
    - unless: ls {{ app_dir }}/static/css/*.css
