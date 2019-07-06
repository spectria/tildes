{% set redis_version = '4.0.9' %}

unpack-redis:
  archive.extracted:
    - name: /tmp/redis-{{ redis_version }}
    - source:
      - salt://redis/{{ redis_version }}.tar.gz
      - https://github.com/antirez/redis/archive/{{ redis_version }}.tar.gz
    - source_hash: sha256=e18eebc08a4ccf48ac28aed692c69cf7b03f188d890803e7ccc6889c049f10b4
    - unless: /usr/local/bin/redis-server --version | grep v={{ redis_version }}
    - options: --strip-components=1
    - enforce_toplevel: False

install-redis:
  pkg.installed:
    - pkgs:
      - build-essential
  cmd.run:
    - cwd: /tmp/redis-{{ redis_version }}/
    - names:
      - make
      - make install
    - onchanges:
      - archive: unpack-redis

redis-user:
  group.present:
    - name: redis
  user.present:
    - name: redis
    - groups: [redis]
    - createhome: False

/run/redis:
  file.directory:
    - user: redis
    - group: redis
    - mode: 755
    - require:
      - user: redis-user

/var/lib/redis:
  file.directory:
    - user: redis
    - group: redis
    - mode: 700
    - require:
      - user: redis-user

/var/log/redis:
  file.directory:
    - user: redis
    - group: redis
    - mode: 744
    - require:
      - user: redis-user

/etc/redis.conf:
  file.managed:
    - source: salt://redis/redis.conf.jinja2
    - template: jinja
    - user: redis
    - group: redis
    - mode: 600
    - require:
      - user: redis-user

/etc/systemd/system/redis.service:
  file.managed:
    - source: salt://redis/redis.service
    - user: root
    - group: root
    - mode: 644
    - require_in:
      - service: redis.service

# add the service file for disabling transparent hugepage
/etc/systemd/system/transparent_hugepage.service:
  file.managed:
    - source: salt://redis/transparent_hugepage.service
    - user: root
    - group: root
    - mode: 644
    - require_in:
      - service: disable-transparent-hugepage

# enable the "disable transparent hugepage" service and run it
disable-transparent-hugepage:
  service.enabled:
    - name: transparent_hugepage.service
  cmd.run:
    - name: systemctl start transparent_hugepage.service
    - unless: 'cat /sys/kernel/mm/transparent_hugepage/enabled | grep \\[never\\]'
    - require_in:
      - service: redis.service
    - watch_in:
      - service: redis.service

# Set kernel overcommit mode (recommended for Redis)
overcommit-memory:
  # will take effect immediately
  cmd.run:
    - name: sysctl vm.overcommit_memory=1
    - unless: sysctl -n vm.overcommit_memory | grep 1

  # makes the setting permanent but requires a restart
  file.append:
    - name: /etc/sysctl.conf
    - text: 'vm.overcommit_memory = 1'

redis.service:
  service.running:
    - enable: True
    - watch:
      - file: /etc/redis.conf
    - require:
      - user: redis-user
      - cmd: install-redis
