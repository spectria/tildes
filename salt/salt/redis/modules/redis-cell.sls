redis-cell-unpack:
  archive.extracted:
    - name: /opt/redis-cell
    - source:
      - salt://redis/modules/redis-cell-v0.2.1-x86_64-unknown-linux-gnu.tar.gz
      - https://github.com/brandur/redis-cell/releases/download/v0.2.1/redis-cell-v0.2.1-x86_64-unknown-linux-gnu.tar.gz
    - source_hash: sha256=9427fb100f4cada817f30f854ead7f233de32948a0ec644f15988c275a2ed1cb
    - if_missing: /opt/redis-cell
    - enforce_toplevel: False
    - require_in:
      - service: redis.service

redis-cell-loadmodule-line:
  file.accumulated:
    - name: redis_loadmodule_lines
    - filename: /etc/redis.conf
    - text:
      - 'loadmodule /opt/redis-cell/libredis_cell.so'
    - require_in:
      - file: /etc/redis.conf
