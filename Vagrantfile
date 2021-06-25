# -*- mode: ruby -*-
# vi: set ft=ruby :

VAGRANT_CONFIG_VERSION = "2"

Vagrant.configure(VAGRANT_CONFIG_VERSION) do |config|
  # Using the "contrib" version for vboxsf module for synced folders
  config.vm.box = "debian/contrib-buster64"

  # Main application folder
  config.vm.synced_folder "tildes/", "/opt/tildes/"

  config.vm.synced_folder "ansible/", "/srv/ansible"

  config.vm.network "forwarded_port", guest: 443, host: 4443
  config.vm.network "forwarded_port", guest: 9090, host: 9090

  config.vm.provision "ansible_local" do |ansible|
    ansible.install_mode = "pip"

    # Since Debian Buster still uses Python 2.7 by default and the pip bootstrap
    # script is no longer compatible with 2.7, we need to specify the installation
    # command manually. If we upgrade to a newer version of Debian that defaults to
    # Python 3.6+, this should no longer be necessary.
    ansible.pip_install_cmd = "sudo apt-get install -y python3-distutils && curl -s https://bootstrap.pypa.io/get-pip.py | sudo python3"

    # Vagrant doesn't currently recognize the new format for Ansible versions
    # (e.g. "ansible [core 2.11.1]"), so the compatibility mode is set incorrectly.
    # A new version of Vagrant should resolve this soon.
    ansible.compatibility_mode = "2.0"

    # put the VM into the "dev" and "app_server" Ansible groups
    ansible.groups = {
        "dev" => ["default"],
        "app_server" => ["default"],
    }

    ansible.galaxy_role_file = "ansible/requirements.yml"
    ansible.playbook = "ansible/playbook.yml"
  end

  config.vm.provider "virtualbox" do |vb|
      vb.memory = "4096"
      vb.cpus = "4"
  end
end
