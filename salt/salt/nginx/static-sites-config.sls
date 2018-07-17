/etc/nginx/sites-available/tildes-static-sites.conf:
  file.managed:
    - source: salt://nginx/tildes-static-sites.conf.jinja2
    - template: jinja
    - user: root
    - group: root
    - mode: 644
    - makedirs: True

/etc/nginx/sites-enabled/tildes-static-sites.conf:
  file.symlink:
    - target: /etc/nginx/sites-available/tildes-static-sites.conf
    - makedirs: True
    - user: root
    - group: root
    - mode: 644
