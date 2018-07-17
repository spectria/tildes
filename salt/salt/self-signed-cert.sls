self-signed-cert:
  pkg.installed:
    - name: python3-openssl
  module.run:
    - tls.create_self_signed_cert:
      - days: 3650
    - require:
      - pkg: python3-openssl
    - unless: ls /etc/pki/tls/certs/localhost.key
  file.managed:
    - name: /etc/pki/tls/certs/localhost.key
    - mode: 600
    - replace: False
    - require:
      - module: self-signed-cert
    - require_in:
      - service: nginx
