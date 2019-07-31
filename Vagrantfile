Vagrant.configure(2) do |config|
  config.vm.define "pwyf" do |normal|

    config.vm.box = "ubuntu/bionic64"

    config.vm.network "forwarded_port", guest: 5000, host: 5000

    config.vm.provider "virtualbox" do |vb|
      vb.gui = false
      vb.memory = "2048"

    end

    config.vm.provision :shell, path: "vagrant/bootstrap.sh"

  end

end
