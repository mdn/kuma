Vagrant.require_version ">= 1.7.2"

plugins = [
    'vagrant-hostsupdater',
    'vagrant-env',
    'vagrant-vbguest',
    'vagrant-cachier',
]
plugins.each do |plugin|
    if !Vagrant.has_plugin?(plugin)
        system("vagrant plugin install #{plugin}")
    end
end

Vagrant.configure('2') do |config|
    config.env.enable

    if Vagrant::Util::Platform.windows?
      NFS = false
    else
      NFS = (ENV['VAGRANT_NFS'] || 'true') == 'true'
    end

    MEMORY_SIZE = (ENV['VAGRANT_MEMORY_SIZE'] || '2048').to_i
    CPU_CORES = (ENV['VAGRANT_CPU_CORES'] || '2').to_i
    IP = ENV['VAGRANT_IP'] || '192.168.10.55'
    GUI = (ENV['VAGRANT_GUI'] || 'false') == 'true'
    ANSIBLE_VERBOSE = (ENV['VAGRANT_ANSIBLE_VERBOSE'] || 'false') == 'true'
    USE_CACHIER = (ENV['VAGRANT_CACHIER'] || 'false') == 'true'

    config.package.name = 'kuma-ubuntu.box'
    config.vm.box = 'ubuntu/trusty64'
    config.vm.define 'developer-local'
    config.vm.network :private_network, ip: IP
    # Vagrant will mangle the line for 127.0.0.1 in the VM's /etc/hosts if this option is set.
    # config.vm.hostname = 'developer-local.allizom.org'
    config.hostsupdater.aliases = ['developer-local.allizom.org', 'mdn-local.mozillademos.org']
    config.ssh.forward_agent = true

    if USE_CACHIER
        config.cache.scope = :box
        config.cache.auto_detect = false
        config.cache.enable :apt
        config.cache.enable :apt_lists
        config.cache.enable :gem
        config.cache.enable :generic, {
            "pip" => { cache_dir: "/root/.cache/pip" },
            "product_details" => { cache_dir: "/home/vagrant/product_details_json" },
        }
    end
    if NFS and USE_CACHIER
        config.cache.synced_folder_opts = {
            type: :nfs,
            # The nolock option can be useful for an NFSv3 client that wants to avoid the
            # NLM sideband protocol. Without this option, apt-get might hang if it tries
            # to lock files needed for /var/cache/* operations. All of this can be avoided
            # by using NFSv4 everywhere. Please note that the tcp option is not the default.
            mount_options: ['rw', 'vers=3', 'tcp', 'nolock']
        }
    end

    # nfs needs to be explicitly enabled to run.
    config.vm.synced_folder '.', '/vagrant', :disabled => true
    config.vm.synced_folder '.', '/home/vagrant/src', :nfs => NFS

    config.vm.provider :virtualbox do |vb, override|
        vb.customize ['modifyvm', :id, '--ostype', 'Ubuntu_64']
        vb.customize ['modifyvm', :id, '--ioapic', 'on']
        vb.customize ['modifyvm', :id, '--memory', MEMORY_SIZE]
        vb.customize ['modifyvm', :id, '--cpus', CPU_CORES]

        # This thing can be a little hungry for memory
        # uncomment to enable VM GUI console, mainly for troubleshooting
        if GUI
            vb.boot_mode = :gui
        end
    end

    config.vm.provision :ansible do |ansible|
        ansible.playbook = 'provisioning/vagrant.yml'
        ansible.sudo = true
        if ANSIBLE_VERBOSE
          ansible.verbose = 'vvvv'
        end
    end
end
