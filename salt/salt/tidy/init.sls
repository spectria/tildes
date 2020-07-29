{% set tidy_version = '5.7.28' %}

unpack-tidy:
  archive.extracted:
    - name: /tmp/tidy-{{ tidy_version }}
    - source:
      - https://github.com/htacg/tidy-html5/archive/{{ tidy_version }}.tar.gz
    - source_hash: sha256=5caa2c769204f506e24ea4986a45abe23f71d14f0fe968314f20065f342ffdba
    - unless: /usr/local/bin/tidy --version | grep 'version {{ tidy_version }}'
    - options: --strip-components=1
    - enforce_toplevel: False

install-tidy:
  pkg.installed:
    - pkgs:
      - build-essential
  cmd.run:
    - cwd: /tmp/tidy-{{ tidy_version }}/build/cmake
    - names:
      - cmake ../.. -DCMAKE_BUILD_TYPE=Release
      - make
      - make install
      - ldconfig
    - onchanges:
      - archive: unpack-tidy
