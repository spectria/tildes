{% from 'common.jinja2' import app_dir, app_username, bin_dir %}

data-cleanup-cronjob:
  cron.present:
    - name: {{ bin_dir }}/python -c "from scripts.clean_private_data import clean_all_data; clean_all_data('{{ app_dir }}/{{ pillar['ini_file'] }}')"
    - hour: 4
    - minute: 10

generate-site-icons-cronjob:
  cron.present:
    - name: /usr/local/bin/generate-site-icons
    - user: {{ app_username }}
    - minute: '*/5'
