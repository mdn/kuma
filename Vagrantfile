#
# Vagrant setup for Kuma
#
Vagrant::Config.run do |config|

    # This should get you a mostly ready-baked base box
    config.vm.box = "kuma"
    config.vm.box_url = "http://people.mozilla.com/~lorchard/vm/kuma.box"
    config.package.name = "kuma.box"

    # To rebuild from mostly scratch, use this CentOS 5.6 (32 bit) image:
    # config.vm.box = "centos-56-32"
    # config.vm.box_url = "http://people.mozilla.com/~lorchard/vm/centos-56-32.box"

    # Plain old VirtualBox shared folder in use here:
    config.vm.share_folder("v-root", "/vagrant", ".")

    # On OS X and Linux you can use an NFS mount; virtualbox shared folders are slow.
    # see also: http://vagrantup.com/docs/nfs.html
    # config.vm.share_folder("v-root", "/vagrant", ".", :nfs => true)

    # This thing can be a little hungry for memory
    config.vm.customize do |vm|
        vm.memory_size = 768
    end

    # Increase vagrant's patience during hang-y CentOS bootup
    # see: https://github.com/jedi4ever/veewee/issues/14
    config.ssh.max_tries = 50
    config.ssh.timeout   = 300

    # uncomment to enable VM GUI console, mainly for troubleshooting
    #config.vm.boot_mode = :gui

    # Add to /etc/hosts: 192.168.10.55 developer-dev.mozilla.org
    config.vm.network("192.168.10.55")

    config.vm.provision :puppet do |puppet|
        puppet.manifests_path = "puppet/manifests"
        puppet.manifest_file = "dev-vagrant.pp"
    end

end
