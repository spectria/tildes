{% from 'common.jinja2' import app_dir, bin_dir %}

data-cleanup-cronjob:
  cron.present:
    - name: {{ bin_dir }}/python -c "from scripts.clean_private_data import clean_all_data; clean_all_data('{{ app_dir }}/{{ pillar['ini_file'] }}')"
    - hour: 4
    - minute: 10
