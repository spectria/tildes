/etc/systemd/system/postgresql_redis_bridge.service:
  file.managed:
    - source: salt://postgresql_redis_bridge.service.jinja2
    - template: jinja
    - user: root
    - group: root
    - mode: 644
    - require:
      - service: redis.service
      - service: postgresql

postgresql_redis_bridge.service:
  service.running:
    - enable: True
