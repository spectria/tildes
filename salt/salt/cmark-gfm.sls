unpack-cmark-gfm:
  archive.extracted:
    - name: /tmp/cmark-gfm
    - source:
      - salt://cmark-gfm.tar.gz
      - https://github.com/github/cmark-gfm/archive/0.29.0.gfm.0.tar.gz
    - source_hash: sha256=6a94aeaa59a583fadcbf28de81dea8641b3f56d935dda5b2447a3c8df6c95fea
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
