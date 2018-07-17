/usr/local/bin/activate:
  file.managed:
    - source: salt://scripts/activate.sh.jinja2
    - template: jinja
    - user: root
    - group: root
    - mode: 755
