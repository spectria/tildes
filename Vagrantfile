# -*- mode: ruby -*-
# vi: set ft=ruby :

VAGRANT_CONFIG_VERSION = "2"

Vagrant.configure(VAGRANT_CONFIG_VERSION) do |config|
  config.vm.box = "ubuntu/xenial64"

  # Main application folder
  config.vm.synced_folder "tildes/", "/opt/tildes/"

  # Mount the salt file root and pillar root
  config.vm.synced_folder "salt/salt/", "/srv/salt/"
  config.vm.synced_folder "salt/pillar/", "/srv/pillar/"

  config.vm.network "forwarded_port", guest: 443, host: 4443
  config.vm.network "forwarded_port", guest: 9090, host: 9090

  # Masterless salt provisioning
  config.vm.provision :salt do |salt|
      salt.masterless = true
      salt.minion_config = "salt/minion"
      salt.run_highstate = true
      salt.verbose = true
      salt.log_level = "info"
  end

  config.vm.provider "virtualbox" do |vb|
      vb.memory = "4096"
      vb.cpus = "4"
  end
end
