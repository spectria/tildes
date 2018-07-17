rebloom-clone:
  git.latest:
    - name: https://github.com/RedisLabsModules/rebloom
    - rev: 4947c9a75838688df56fc818729b93bf36588400
    - target: /opt/rebloom

rebloom-make:
  cmd.run:
    - name: make
    - cwd: /opt/rebloom
    - onchanges:
      - git: rebloom-clone
    - require_in:
      - service: redis_breached_passwords.service
