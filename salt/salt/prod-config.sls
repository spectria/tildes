# Force apt not to use IPv6 (seems to hang often)
/etc/apt/apt.conf.d/99force-ipv4:
  file.managed:
    - contents: 'Acquire::ForceIPv4 "true";'
