Vagrant::Config.run do |config|

    # To rebuild from mostly scratch, use:
    config.vm.box = "puppet-centos-55-64"
    config.vm.box_url = "http://puppetlabs.s3.amazonaws.com/pub/centos5_64.box"
    config.vm.share_folder("v-root", "/vagrant", ".") # No NFS in base box.

    # Need to use an NFS mount; virtualbox shared folders are super-slow
    # see also: http://vagrantup.com/docs/nfs.html
    # config.package.name = "kuma"
    # config.vm.box = "kuma"
    # config.vm.share_folder("v-root", "/vagrant", ".", :nfs => true)

    # Switch someday to this, to more closely match production?
    # config.vm.share_folder("v-root2", "/data/dekiwiki_python/src/developer.mozilla.org/mdn", 
    #    ".", :nfs => true)

    # This thing can be a little hungry for memory
    config.vm.customize do |vm|
        vm.memory_size = 768
    end

    # uncomment to enable VM GUI console
    # config.vm.boot_mode = :gui
 
    # Add to /etc/hosts: 192.168.10.50 dev-kuma.developer.mozilla.org
    config.vm.network("192.168.10.50")

    config.vm.provision :puppet do |puppet|
        puppet.manifests_path = "puppet/manifests"
        puppet.manifest_file = "mozilla_kuma.pp"
    end

end
