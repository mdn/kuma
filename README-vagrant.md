# Kuma in VirtualBox via Vagrant

This is an attempt to describe the bootstrap process to get Kuma running in a
Vagrant-managed virtual machine. 

This is known to work on Mac OS X. It could possibly be made to work under
Linux and Windows, but I haven't tried. Bug reports and suggestions are
welcome. The main barrier to Windows is probably that this Vagrantfile 
[uses NFS to share the current working directory][nfs] for performance 
reasons. 

[nfs]: http://vagrantup.com/docs/nfs.html

    # Install VirtualBox 4 from http://www.virtualbox.org/

    # Open a terminal window.
    
    # Install vagrant, see vagrantup.com
    # NOTE: Currently, vagrant v0.8.8 appears to fail with this setup, so we
    # need to revert to 0.8.7
    sudo gem update
    sudo gem install vagrant --version=0.8.7
        
    # Fire up the VM and install everything, go take a bike ride (approx. 15 min)
    # Clone a Kuma repo, switch to "mdn" branch (for now)
    git clone git://github.com/mozilla/kuma.git
    cd kuma
    git checkout mdn
    git submodule update --init --recursive

    # Fire up the VM and install everything, take a bike ride (approx. 30 min)
    vagrant up

    # If the process fails with an error, try running the Puppet setup again.
    # (This sometimes fixes transient or ordering problems)
    vagrant provision

    # Add developer-dev.mozilla.org to /etc/hosts
    echo '192.168.10.55 developer-dev.mozilla.org' >> /etc/hosts

    # Everything should be working now.
    curl 'http://developer-dev.mozilla.org'
    
    # Experimental / Optional: Download and import data extracted from the
    # production site. This can take a long while, since there's over 500MB
    vagrant ssh
    sudo puppet apply /vagrant/puppet/manifests/dev-vagrant-mdn-import.pp
    mysql -uroot < /vagrant/puppet/files/tmp/postimport.sql
    sudo puppet apply /vagrant/puppet/manifests/dev-vagrant.pp

    # Edit files as usual on your host machine; the current directory is
    # mounted via NFS at /vagrant within the VM.

    # Useful vagrant sub-commands:

    vagrant ssh     # Connect to the VM via ssh
    vagrant suspend # Sleep the VM, saving state
    vagrant halt    # Shutdown the VM
    vagrant up      # Boot up the VM
    vagrant destroy # Destroy the VM

    # Occasionally run this within the VM to sync the environment up 
    # with an updated Puppet manifest, or to recover from failures
    # during the initial VM spin-up. It should be safe to run repeatedly,
    # since Puppet works to establish state, not run scripts per se.

    sudo puppet apply /vagrant/puppet/manifests/dev-vagrant-mdn.pp
