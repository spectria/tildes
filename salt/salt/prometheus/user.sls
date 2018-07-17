prometheus-user:
  group.present:
    - name: prometheus
  user.present:
    - name: prometheus
    - groups: [prometheus]
    - createhome: False
