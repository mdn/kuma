# Kuma in VirtualBox via Vagrant

This is an attempt to describe the bootstrap process to get Kuma running in a
Vagrant-managed virtual machine. 

This could possibly be made to work under Linux and Windows, but I haven't
tried. The main barrier to Windows is probably that this Vagrantfile
[uses NFS to share the current working directory][nfs] for performance reasons. 

[nfs]: http://vagrantup.com/docs/nfs.html

    # Install VirtualBox 4 from http://www.virtualbox.org/

    # Open a terminal window.
    
    # Install vagrant, see vagrantup.com
    gem install vagrant
        
    # Clone a Kuma repo, switch to my vagrant branch (for now)
    git clone git://github.com/lmorchard/kuma.git
    cd kuma

    # Check out the "mdn" branch (for now)    
    git checkout mdn

    # Fire up the VM and install everything, go take a bike ride (approx. 15 min)
    vagrant up
    
    # Add dev-kuma.developer.mozilla.org to /etc/hosts
    sudo su
    echo '192.168.10.50 dev-kuma.developer.mozilla.org' >> /etc/hosts
    exit
    # (or, you know, sudo vi /etc/hosts and do it by hand)

    # Everything should be working now.
    curl 'http://dev-kuma.developer.mozilla.org'

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

    sudo puppet apply /vagrant/puppet/manifests/mozilla_kuma.pp

    # caveat: Do not run this while /vagrant is the current working directory. 
    # The puppet/ directory there seems to cause issues. (FIXME)
