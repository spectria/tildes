/etc/systemd/system/consumer-topic_interesting_activity_updater.service:
  file.managed:
    - source: salt://consumers/topic_interesting_activity_updater.service.jinja2
    - template: jinja
    - user: root
    - group: root
    - mode: 644

/etc/systemd/system/consumer-topic_metadata_generator.service:
  file.managed:
    - source: salt://consumers/topic_metadata_generator.service.jinja2
    - template: jinja
    - user: root
    - group: root
    - mode: 644

/etc/systemd/system/consumer-comment_user_mentions_generator.service:
  file.managed:
    - source: salt://consumers/comment_user_mentions_generator.service.jinja2
    - template: jinja
    - user: root
    - group: root
    - mode: 644

consumer-topic_interesting_activity_updater.service:
  service.running:
    - enable: True

consumer-topic_metadata_generator.service:
  service.running:
    - enable: True

consumer-comment_user_mentions_generator.service:
  service.running:
    - enable: True

{% if grains['id'] == 'prod' %}
/etc/systemd/system/consumer-topic_embedly_extractor.service:
  file.managed:
    - source: salt://consumers/topic_embedly_extractor.service.jinja2
    - template: jinja
    - user: root
    - group: root
    - mode: 644

consumer-topic_embedly_extractor.service:
  service.running:
    - enable: True

/etc/systemd/system/consumer-topic_youtube_scraper.service:
  file.managed:
    - source: salt://consumers/topic_youtube_scraper.service.jinja2
    - template: jinja
    - user: root
    - group: root
    - mode: 644

consumer-topic_youtube_scraper.service:
  service.running:
    - enable: True

/etc/systemd/system/consumer-site_icon_downloader.service:
  file.managed:
    - source: salt://consumers/site_icon_downloader.service.jinja2
    - template: jinja
    - user: root
    - group: root
    - mode: 644

consumer-site_icon_downloader.service:
  service.running:
    - enable: True
{% endif %}
