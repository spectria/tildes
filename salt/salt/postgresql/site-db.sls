site-db-user:
  postgres_user.present:
    - name: tildes
    - require:
      - service: postgresql

site-db-database:
  postgres_database.present:
    - name: tildes
    - owner: tildes
    - require:
      - postgres_user: tildes

site-db-enable-citext:
  postgres_extension.present:
    - name: citext
    - maintenance_db: tildes
    - require:
      - postgres_database: tildes

site-db-enable-ltree:
  postgres_extension.present:
    - name: ltree
    - maintenance_db: tildes
    - require:
      - postgres_database: tildes

site-db-enable-intarray:
  postgres_extension.present:
    - name: intarray
    - maintenance_db: tildes
    - require:
      - postgres_database: tildes

site-db-enable-pg_stat_statements:
  postgres_extension.present:
    - name: pg_stat_statements
    - maintenance_db: tildes
    - require:
      - postgres_database: tildes

site-db-enable-pg_trgm:
  postgres_extension.present:
    - name: pg_trgm
    - maintenance_db: tildes
    - require:
      - postgres_database: tildes

site-db-pg_hba-lines:
  file.accumulated:
    - name: pg_hba_lines
    - filename: /etc/postgresql/{{ pillar['postgresql_version'] }}/main/pg_hba.conf
    - text:
      - 'local   sameuser        tildes   trust'
    - require_in:
      - file: /etc/postgresql/{{ pillar['postgresql_version'] }}/main/pg_hba.conf

site-db-pgbouncer-lines:
  file.accumulated:
    - name: pgbouncer_db_lines
    - filename: /etc/pgbouncer/pgbouncer.ini
    - text: 'tildes ='
    - require_in:
      - file: /etc/pgbouncer/pgbouncer.ini
