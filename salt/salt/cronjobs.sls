{% from 'common.jinja2' import app_dir, app_username, bin_dir %}

close-voting-cronjob:
  cron.present:
    - name: {{ bin_dir }}/python -c "from scripts.close_voting_on_old_posts import close_voting_on_old_posts; close_voting_on_old_posts('{{ app_dir }}/{{ pillar['ini_file'] }}')"
    - user: {{ app_username }}
    - hour: '*'
    - minute: 3

data-cleanup-cronjob:
  cron.present:
    - name: {{ bin_dir }}/python -c "from scripts.clean_private_data import clean_all_data; clean_all_data('{{ app_dir }}/{{ pillar['ini_file'] }}')"
    - hour: 4
    - minute: 10

generate-site-icons-css-cronjob:
  cron.present:
    - name: {{ bin_dir }}/python -c "from scripts.generate_site_icons_css import generate_css; generate_css()"
    - user: {{ app_username }}
    - minute: '*/5'

post-scheduled-topics-cronjob:
  cron.present:
    - name: {{ bin_dir }}/python -c "from scripts.post_scheduled_topics import post_scheduled_topics; post_scheduled_topics('{{ app_dir }}/{{ pillar['ini_file'] }}')"
    - user: {{ app_username }}

update-common-topic-tags-cronjob:
  cron.present:
    - name: {{ bin_dir }}/python -c "from scripts.update_groups_common_topic_tags import update_common_topic_tags; update_common_topic_tags('{{ app_dir }}/{{ pillar['ini_file'] }}')"
    - user: {{ app_username }}
    - hour: '*'
    - minute: 0
