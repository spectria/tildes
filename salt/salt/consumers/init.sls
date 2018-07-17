/etc/systemd/system/consumer-topic_metadata_generator.service:
  file.managed:
    - source: salt://consumers/topic_metadata_generator.service.jinja2
    - template: jinja
    - user: root
    - group: root
    - mode: 644

consumer-topic_metadata_generator.service:
  service.running:
    - enable: True
