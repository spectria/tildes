compile-pts-lbsearch:
  file.managed:
    - name: /tmp/pts_lbsearch.c
    - source:
      - https://raw.githubusercontent.com/pts/pts-line-bisect/2ecd9f59246cfa28cb1aeac7cd8d98a8eea2914f/pts_lbsearch.c
    - source_hash: sha256=ef79efc2f1ecde504b6074f9c89bdc71259a833fa2a2dda4538ed5ea3e04aea1
    - creates: /usr/local/bin/pts_lbsearch
  cmd.run:
    - cwd: /tmp/
    # compilation command taken from the top of the source file
    - name: gcc -ansi -W -Wall -Wextra -Werror=missing-declarations -s -O2 -DNDEBUG -o /usr/local/bin/pts_lbsearch pts_lbsearch.c
    - creates: /usr/local/bin/pts_lbsearch
