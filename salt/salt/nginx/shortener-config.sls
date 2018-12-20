/etc/nginx/sites-available/tildes-shortener.conf:
  file.managed:
    - source: salt://nginx/tildes-shortener.conf.jinja2
    - template: jinja
    - user: root
    - group: root
    - mode: 644
    - makedirs: True

/etc/nginx/sites-enabled/tildes-shortener.conf:
  file.symlink:
    - target: /etc/nginx/sites-available/tildes-shortener.conf
    - makedirs: True
    - user: root
    - group: root
    - mode: 644
