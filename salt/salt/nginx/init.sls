nginx:
  pkgrepo.managed:
    - name: deb http://nginx.org/packages/ubuntu/ xenial nginx
    - dist: xenial
    - file: /etc/apt/sources.list.d/nginx.list
    - key_url: https://nginx.org/keys/nginx_signing.key
    - require_in:
      - pkg: nginx
  pkg.installed:
    - name: nginx
    - refresh: True
  service.running:
    - require:
      - pkg: nginx
    - reload: True
    - watch:
      - file: /etc/nginx/*

/etc/nginx/nginx.conf:
  file.managed:
    - source: salt://nginx/nginx.conf.jinja2
    - template: jinja
    - user: root
    - group: root
    - mode: 644

# Add logrotate config to rotate daily and delete after 30 days
/etc/logrotate.d/nginx:
  file.managed:
    - source: salt://nginx/logrotate
    - user: root
    - group: root
    - mode: 644
