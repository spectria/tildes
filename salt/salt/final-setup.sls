{% from 'common.jinja2' import app_dir, bin_dir %}

initialize-db:
  cmd.run:
    - name: {{ bin_dir }}/python -c "from scripts.initialize_db import initialize_db; initialize_db('{{ app_dir }}/{{ pillar['ini_file'] }}')"
    - cwd: {{ app_dir }}
    - onchanges:
      - postgres_database: tildes

{% if grains['id'] == 'dev' %}
insert-dev-data:
  cmd.run:
    - name: {{ bin_dir }}/python -c "from scripts.initialize_db import insert_dev_data; insert_dev_data('{{ app_dir }}/{{ pillar['ini_file'] }}')"
    - cwd: {{ app_dir }}
    - onchanges:
      - cmd: initialize-db
{% endif %}
