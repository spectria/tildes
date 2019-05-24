{% from 'common.jinja2' import app_username %}

# Create the base directory for the wiki files and initialize a git repo
/var/lib/tildes-wiki:
  file.directory:
    - user: {{ app_username }}
    - group: {{ app_username }}
    - mode: 775
  git.present:
    - bare: False
    - user: {{ app_username }}

# Create the initial (empty) commit in the new git repo
wiki-initial-commit:
  cmd.run:
    - names:
      - git config user.name "Tildes"
      - git config user.email "Tildes"
      - git commit --allow-empty -m "Initial commit"
    - cwd: /var/lib/tildes-wiki
    - runas: {{ app_username }}
    - onchanges:
      - file: /var/lib/tildes-wiki
