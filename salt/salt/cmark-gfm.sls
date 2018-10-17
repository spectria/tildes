unpack-cmark-gfm:
  archive.extracted:
    - name: /tmp/cmark-gfm
    - source:
      - salt://cmark-gfm.tar.gz
      - https://github.com/github/cmark/archive/0.28.0.gfm.11.tar.gz
    - source_hash: sha256=8100698cd6fa4e3d870d9c7fbf92ef795a60ea3d7b00e3a4d1904105b1191fae
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
