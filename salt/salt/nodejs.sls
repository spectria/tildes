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
