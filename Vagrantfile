Vagrant::Config.run do |config|

    # uncomment to enable VM GUI console
    # config.vm.boot_mode = :gui

    # Need to use an NFS mount; virtualbox shared folders are super-slow
    # see also: http://vagrantup.com/docs/nfs.html
    config.vm.share_folder("v-root", "/vagrant", ".", :nfs => true)

    # To rebuild from mostly scratch, use:
    config.vm.box = "puppet-centos-55-64"
    config.vm.box_url = "http://puppetlabs.s3.amazonaws.com/pub/centos5_64.box"
    config.vm.share_folder("v-root", "/vagrant", ".") # No NFS in base box.

    # THE FUTURE!!!1!!!!1!1one
    # config.vm.box = "puppet-rhel-6-64"
    # config.vm.box_url = "http://puppetlabs.s3.amazonaws.com/pub/rhel60_64.box"
 
    # Add to /etc/hosts: 192.168.10.50 dev-kuma.developer.mozilla.org
    config.vm.network("192.168.10.50")

    config.vm.provision :puppet do |puppet|
        puppet.manifests_path = "puppet/manifests"
        puppet.manifest_file = "mozilla_kuma.pp"
    end

end
