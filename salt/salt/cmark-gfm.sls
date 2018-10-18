unpack-cmark-gfm:
  archive.extracted:
    - name: /tmp/cmark-gfm
    - source:
      - salt://cmark-gfm.tar.gz
      - https://github.com/github/cmark-gfm/archive/0.28.3.gfm.19.tar.gz
    - source_hash: sha256=d2c8cb255e227d07533a32cfd4a052e189f697e2a9681d8b17d15654259e2e4b
    - if_missing: /usr/local/lib/libcmark-gfm.so
    - options: --strip-components=1
    - enforce_toplevel: False

install-cmark-build-deps:
  pkg.installed:
    - name: cmake

install-cmark-gfm:
  cmd.run:
    - cwd: /tmp/cmark-gfm/
    - names:
      - make
      - make install
    - onchanges:
      - archive: unpack-cmark-gfm
    - require:
      - pkg: install-cmark-build-deps
