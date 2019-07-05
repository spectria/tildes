{% from "common.jinja2" import app_dir, app_username %}

# Add the NodeSource repository and install Node.js 10.x
nodejs-pkgrepo:
  pkgrepo.managed:
    - name: deb https://deb.nodesource.com/node_10.x xenial main
    - dist: xenial
    - file: /etc/apt/sources.list.d/nodesource.list
    - key_url: https://deb.nodesource.com/gpgkey/nodesource.gpg.key
    - require_in:
      - pkg: nodejs
  pkg.installed:
    - name: nodejs
    - refresh: True

# Install the npm packages defined in package.json
# Uses the --no-bin-links option to prevent npm from creating symlinks in the .bin
# directory, which doesn't work inside Vagrant on Windows
install-npm-packages:
  cmd.run:
    - name: npm install --no-bin-links
    - cwd: {{ app_dir }}
    - runas: {{ app_username }}
    - require:
      - pkg: nodejs
