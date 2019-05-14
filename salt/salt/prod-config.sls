# Force apt not to use IPv6 (seems to hang often)
/etc/apt/apt.conf.d/99force-ipv4:
  file.managed:
    - contents: 'Acquire::ForceIPv4 "true";'

# Enable ipv6 networking
/etc/network/interfaces:
  file.append:
    - text: |
        iface eth0 inet6 static
            address {{ pillar['ipv6_address'] }}
            netmask 64

        post-up sleep 5; /sbin/ip -family inet6 route add {{ pillar['ipv6_gateway'] }} dev eth0
        post-up sleep 5; /sbin/ip -family inet6 route add default via {{ pillar['ipv6_gateway'] }}
        pre-down /sbin/ip -family inet6 route del default via {{ pillar['ipv6_gateway'] }}
        pre-down /sbin/ip -family inet6 route del {{ pillar['ipv6_gateway'] }} dev eth0
