erlang:
  pkgrepo.managed:
    - name: deb http://packages.erlang-solutions.com/ubuntu/ xenial contrib
    - dist: xenial
    - file: /etc/apt/sources.list.d/erlang.list
    - key_url: https://packages.erlang-solutions.com/ubuntu/erlang_solutions.asc
    - require_in:
      - pkg: rabbitmq-server
  file.managed:
    - name: /etc/apt/preferences.d/erlang
    - mode: 755
    - contents: |
        Package: erlang*
        Pin: version 1:20.3-1
        Pin-Priority: 1000
    - require_in:
      - pkg: rabbitmq-server

rabbitmq:
  pkgrepo.managed:
    - name: deb http://www.rabbitmq.com/debian/ testing main
    - dist: testing
    - file: /etc/apt/sources.list.d/rabbitmq.list
    - key_url: https://www.rabbitmq.com/rabbitmq-release-signing-key.asc
    - require_in:
      - pkg: rabbitmq-server
  pkg.installed:
    - name: rabbitmq-server
    - refresh: True

rabbitmq-server.service:
  service.running:
    - enable: True
    - watch:
      - file: /etc/rabbitmq/rabbitmq.config
      - file: /etc/rabbitmq/definitions.json

rabbitmq-management:
  cmd.run:
    - name: rabbitmq-plugins enable rabbitmq_management
    - unless: 'rabbitmq-plugins list | grep \\[E.*rabbitmq_management'

/usr/local/bin/rabbitmqadmin:
  cmd.run:
    - name: wget http://localhost:15672/cli/rabbitmqadmin -O /usr/local/bin/rabbitmqadmin
    - creates: /usr/local/bin/rabbitmqadmin
  file.managed:
    - mode: 755

/etc/rabbitmq/rabbitmq.config:
  file.managed:
    - source: salt://rabbitmq/rabbitmq.config
    - group: rabbitmq
    - mode: 644

/etc/rabbitmq/definitions.json:
  file.managed:
    - source: salt://rabbitmq/definitions.json
    - group: rabbitmq
    - mode: 644

install-pg-amqp-bridge:
  archive.extracted:
    - name: /usr/local/bin
    - source:
      - https://github.com/subzerocloud/pg-amqp-bridge/releases/download/0.0.5/pg-amqp-bridge-0.0.5-x86_64-unknown-linux-gnu.tar.gz
    - source_hash: sha256=8194c3307fe7954a0ef1ba66d2f51e14647756d0f87ddd468ef0dc3fbc8476fe
    - unless: ls /usr/local/bin/pg-amqp-bridge
    - enforce_toplevel: False

/etc/systemd/system/pg-amqp-bridge.service:
  file.managed:
    - source: salt://rabbitmq/pg-amqp-bridge.service
    - user: root
    - group: root
    - mode: 644
    - require_in:
      - pg-amqp-bridge.service

pg-amqp-bridge.service:
  service.running:
    - enable: True
