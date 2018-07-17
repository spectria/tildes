/etc/nginx/sites-available/tildes.conf:
  file.managed:
    - source: salt://nginx/tildes.conf.jinja2
    - template: jinja
    - user: root
    - group: root
    - mode: 644
    - makedirs: True

/etc/nginx/sites-enabled/tildes.conf:
  file.symlink:
    - target: /etc/nginx/sites-available/tildes.conf
    - makedirs: True
    - user: root
    - group: root
    - mode: 644
