unpack-cmark-gfm:
  archive.extracted:
    - name: /tmp/cmark-gfm
    - source:
      - salt://cmark-gfm.tar.gz
      - https://github.com/github/cmark/archive/0.28.0.gfm.11.tar.gz
    - source_hash: sha256=a95ee221c3f6d718bbb38bede95f05f05e07827f8f3c29ed6cb09ddb7d05c2cd
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
