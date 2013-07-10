require "yaml"

# Load up our vagrant config files -- vagrantconfig.yaml first
_config = YAML.load(File.open(File.join(File.dirname(__FILE__),
                    "vagrantconfig.yaml"), File::RDONLY).read)

# Local-specific/not-git-managed config -- vagrantconfig_local.yaml
begin
  _config.merge!(YAML.load(File.open(File.join(File.dirname(__FILE__),
                 "vagrantconfig_local.yaml"), File::RDONLY).read))
rescue Errno::ENOENT # No vagrantconfig_local.yaml found -- that's OK; just
                     # use the defaults.
end

CONF = _config
MOUNT_POINT = "/vagrant"

Vagrant.configure("2") do |config|
  
    config.vm.box = CONF['box']
    config.vm.box_url = CONF['box_url']
    config.vm.network :private_network, ip: CONF['ip_address']
    config.package.name = CONF['package_name']
  
    # nfs needs to be explicitly enabled to run.
    if CONF['nfs'] == false or RUBY_PLATFORM =~ /mswin(32|64)/
        config.vm.synced_folder ".", MOUNT_POINT
    else
        config.vm.synced_folder ".", MOUNT_POINT, :nfs => true
    end
  
    config.vm.provider :virtualbox do |vb|
        vb.customize ["modifyvm", :id, "--memory", CONF['memory_size']]
        vb.customize ['modifyvm', :id, '--ostype', 'Ubuntu_64']
        # This thing can be a little hungry for memory
        # uncomment to enable VM GUI console, mainly for troubleshooting
        if CONF['gui'] == true
            vb.boot_mode = :gui
        end
    end
  
    # Increase vagrant's patience during hang-y CentOS bootup
    # see: https://github.com/jedi4ever/veewee/issues/14
    config.ssh.max_tries = 50
    config.ssh.timeout = 300
  
    config.vm.provision :puppet do |puppet|
        puppet.manifests_path = "puppet/manifests"
        puppet.manifest_file = "dev-vagrant.pp"
    end
  
end
