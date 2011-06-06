Vagrant::Config.run do |config|

    # To rebuild from mostly scratch, use this CentOS 5.6 (32 bit) image:
    config.vm.box = "centos-56-32"
    config.vm.box_url = "http://people.mozilla.com/~lorchard/centos-56-32.box"
    config.vm.share_folder("v-root", "/vagrant", ".")

    # This box works, too, but not under a 32-bit host (eg. Ubuntu 32-bit)
    # config.vm.box = "puppet-centos-55-64"
    # config.vm.box_url = "http://puppetlabs.s3.amazonaws.com/pub/centos5_64.box"
    # config.vm.share_folder("v-root", "/vagrant", ".") # No NFS in base box.

    # Once you've gotten a successful initial from-scratch build, export the
    # box for faster destroy/up next time.
    #  $ vagrant package
    #  $ vagrant box add kuma kuma.box
    config.package.name = "kuma.box"

    # Uncomment this line to use your packaged box
    # config.vm.box = "kuma"

    # On OS X and Linux you can use an NFS mount; virtualbox shared folders are slow.
    # see also: http://vagrantup.com/docs/nfs.html
    # config.vm.share_folder("v-root", "/vagrant", ".", :nfs => true)

    # Switch someday to this, to more closely match production?
    # config.vm.share_folder("v-root2", "/data/dekiwiki_python/src/developer.mozilla.org/mdn", 
    #    ".", :nfs => true)

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

    # Add to /etc/hosts: 192.168.10.50 dev-kuma.developer.mozilla.org
    config.vm.network("192.168.10.50")

    config.vm.provision :puppet do |puppet|
        puppet.manifests_path = "puppet/manifests"
        puppet.manifest_file = "mozilla_kuma.pp"
    end

end
