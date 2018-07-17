{% from 'common.jinja2' import app_dir, bin_dir %}

/etc/systemd/system/webassets.service:
  file.managed:
    - source: salt://webassets.service.jinja2
    - template: jinja
    - user: root
    - group: root
    - mode: 644
    - require_in:
      - service: webassets.service

webassets.service:
  service.running:
    - enable: True
    - require:
      - pip: pip-installs
