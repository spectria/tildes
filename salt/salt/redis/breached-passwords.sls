/run/redis_breached_passwords:
  file.directory:
    - user: redis
    - group: redis
    - mode: 755
    - require:
      - user: redis-user

/etc/redis_breached_passwords.conf:
  file.managed:
    - source: salt://redis/redis_breached_passwords.conf
    - user: redis
    - group: redis
    - mode: 600

/etc/systemd/system/redis_breached_passwords.service:
  file.managed:
    - source: salt://redis/redis_breached_passwords.service
    - user: root
    - group: root
    - mode: 644
    - require_in:
      - service: redis_breached_passwords.service

redis_breached_passwords.service:
  service.running:
    - enable: True
    - watch:
      - file: /etc/redis_breached_passwords.conf
