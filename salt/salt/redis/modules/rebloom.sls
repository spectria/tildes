# Take care if updating this module - Redis Labs changed the license on July 16, 2018
# to Apache 2 with their "Commons Clause": https://commonsclause.com/
# The legality and specific implications of that clause are currently unclear, so we
# probably shouldn't update to a version under that license without more research.
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
