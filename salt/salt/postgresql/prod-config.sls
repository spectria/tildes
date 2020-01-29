# Values from PGTune (https://pgtune.leopard.in.ua/)
{% set setting_values = {
    "checkpoint_completion_target": "0.7",
    "default_statistics_target": "100",
    "effective_cache_size": "24GB",
    "effective_io_concurrency": 200,
    "maintenance_work_mem": "2GB",
    "max_parallel_workers": "8",
    "max_parallel_workers_per_gather": "4",
    "max_wal_size": "2GB",
    "max_worker_processes": "8",
    "min_wal_size": "1GB",
    "random_page_cost": "1.1",
    "shared_buffers": "8GB",
    "wal_buffers": "16MB",
    "work_mem": "10485kB",
} %}

{% for setting, value in setting_values.items() %}
postgresql-conf-set-{{ setting }}:
  file.replace:
    - name: /etc/postgresql/{{ pillar['postgresql_version'] }}/main/postgresql.conf
    - pattern: '^#?{{ setting }} = (?!{{ value }}).*$'
    - repl: '{{ setting }} = {{ value }}'
{% endfor %}
