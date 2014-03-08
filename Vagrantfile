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

    config.vm.provider :vmware_fusion do |vmware, override|
        vmware.vmx['memsize'] = CONF['memory_size']
        vmware.vmx['numvcpus'] = CONF['number_cpus']
        override.vm.box_url =  CONF['vmware_box_url']
        # don't use nfs for vmware, since it didn't work for me -- @jezdez
        override.vm.synced_folder ".", CONF['mount_point']
    end

    config.vm.provider :vmware_workstation do |vmware, override|
        vmware.vmx["memsize"] = CONF['memory_size']
        vmware.vmx['numvcpus'] = CONF['number_cpus']
        override.vm.box_url =  CONF['vmware_box_url']
        # don't use nfs for vmware, since it didn't work for me -- @jezdez
        override.vm.synced_folder ".", CONF['mount_point']
    end

    config.vm.provider :virtualbox do |vb, override|
        override.vm.box_url = CONF['virtual_box_url']
        vb.customize ["modifyvm", :id, "--memory", CONF['memory_size']]
        vb.customize ['modifyvm', :id, '--ostype', 'Ubuntu_64']
        vb.customize ['modifyvm', :id, '--cpus', CONF['number_cpus']]

        # This thing can be a little hungry for memory
        # uncomment to enable VM GUI console, mainly for troubleshooting
        if CONF['gui'] == true
            vb.boot_mode = :gui
        end
    end

    # section for https://github.com/mitchellh/vagrant-aws
    config.vm.provider :aws do |aws, override|
      override.vm.box = 'dummy-aws'
      override.vm.box_url = CONF['aws_box_url']
      override.ssh.private_key_path = CONF["aws_ssh_privkey"]
      override.ssh.username = "ubuntu"

      aws.access_key_id = CONF["aws_access_key_id"]
      aws.secret_access_key = CONF["aws_secret_access_key"]
      aws.keypair_name = CONF["aws_keypair_name"]
      aws.region = CONF['aws_region']
      aws.ami = CONF['aws_ami']
      aws.instance_type = CONF['aws_instance_type']

    end

    # section for https://github.com/mitchellh/vagrant-rackspace
    config.vm.provider :rackspace do |rs, override|
      override.vm.box = 'dummy-rackspace'
      override.vm.box_url = CONF['rs_box_url']
      override.ssh.private_key_path = CONF["rs_private_key"]

      rs.username = CONF["rs_username"]
      rs.api_key = CONF["rs_api_key"]
      rs.public_key_path = CONF["rs_public_key"]
      rs.flavor = /512MB/
      rs.image = /Ubuntu/
    end

    config.vm.provision :shell do |shell|
      shell.inline = "mkdir -p /etc/puppet/modules;
                      (puppet module list | grep elasticsearch-elasticsearch) ||
                      puppet module install elasticsearch-elasticsearch"
    end

    config.vm.provision :puppet do |puppet|
        puppet.manifests_path = "puppet/manifests"
        puppet.manifest_file = "dev-vagrant.pp"
    end
end
