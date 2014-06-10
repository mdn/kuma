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

Vagrant.configure("2") do |config|
    config.vm.box = CONF['box']
    config.vm.network :private_network, :ip => CONF['ip_address']
    config.package.name = CONF['package_name']
    config.vm.synced_folder ".", "/vagrant", :disabled => true

    # nfs needs to be explicitly enabled to run.
    if CONF['nfs'] == false or RUBY_PLATFORM =~ /mswin(32|64)/
        config.vm.synced_folder ".", CONF['mount_point']
    else
        config.vm.synced_folder ".", CONF['mount_point'], :nfs => true
    end

    config.vm.provider :virtualbox do |vb, override|
        vb.customize ["modifyvm", :id, "--memory", CONF['memory_size']]
        vb.customize ['modifyvm', :id, '--ostype', 'Ubuntu']
        vb.customize ['modifyvm', :id, '--cpus', CONF['number_cpus']]
        vb.customize ["modifyvm", :id, "--ioapic", "on"]

        # This thing can be a little hungry for memory
        # uncomment to enable VM GUI console, mainly for troubleshooting
        if CONF['gui'] == true
            vb.boot_mode = :gui
        end
    end

    config.vm.provision :shell do |shell|
      shell.inline = "mkdir -p /etc/puppet/modules;
                      puppet module install -f puppetlabs-stdlib;
                      puppet module install -f puppetlabs-apt;
                      puppet module install -f elasticsearch-elasticsearch"
    end

    config.vm.provision :puppet do |puppet|
        puppet.manifests_path = "puppet/manifests"
        puppet.manifest_file = "dev-vagrant.pp"
    end
end
