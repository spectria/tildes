test-db-database:
  postgres_database.present:
    - name: tildes_test
    - owner: tildes
    - require:
      - postgres_user: tildes

test-db-enable-citext:
  postgres_extension.present:
    - name: citext
    - maintenance_db: tildes_test
    - require:
      - postgres_database: tildes_test

test-db-enable-ltree:
  postgres_extension.present:
    - name: ltree
    - maintenance_db: tildes_test
    - require:
      - postgres_database: tildes_test

test-db-enable-intarray:
  postgres_extension.present:
    - name: intarray
    - maintenance_db: tildes_test
    - require:
      - postgres_database: tildes_test

test-db-enable-pg_trgm:
  postgres_extension.present:
    - name: pg_trgm
    - maintenance_db: tildes_test
    - require:
      - postgres_database: tildes_test

test-db-pg_hba-lines:
  file.accumulated:
    - name: pg_hba_lines
    - filename: /etc/postgresql/{{ pillar['postgresql_version'] }}/main/pg_hba.conf
    - text:
      - 'local   tildes_test   tildes   trust'
    - require_in:
      - file: /etc/postgresql/{{ pillar['postgresql_version'] }}/main/pg_hba.conf

test-db-pgbouncer-lines:
  file.accumulated:
    - name: pgbouncer_db_lines
    - filename: /etc/pgbouncer/pgbouncer.ini
    - text: 'tildes_test ='
    - require_in:
      - file: /etc/pgbouncer/pgbouncer.ini
