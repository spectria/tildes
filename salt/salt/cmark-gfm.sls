unpack-cmark-gfm:
  archive.extracted:
    - name: /tmp/cmark-gfm
    - source:
      - salt://cmark-gfm.tar.gz
      - https://github.com/github/cmark-gfm/archive/0.28.3.gfm.17.tar.gz
    - source_hash: sha256=101ccfcd4f0fd8b05c20994006d992f2e81d6f96655afee4c66742ccc21f1f7d
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
