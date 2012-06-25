# Ensure some handy dev tools are available.
class dev_tools {
    package { 
        [ "gcc-c++", "git", "subversion-devel", "mercurial", "vim-enhanced",
            "man", "man-pages", "nfs-utils", "nfs-utils-lib", "telnet", "nc",
            "rsync", "samba", "java-1.6.0-openjdk", "tmux"]:
            ensure => installed;
    }
}

# Do some dirty, dirty things to make development nicer.
class dev_hacks {

    file { "/home/vagrant":
        owner => "vagrant", group => "vagrant", mode => 0755;
    }

    file { 
        [ "/home/vagrant/logs",
            "/home/vagrant/uploads",
            "/home/vagrant/product_details_json",
            "/home/vagrant/mdc_pages" ]:
        ensure => directory,
        owner => "vagrant", group => "vagrant", mode => 0777;
    }

    file { "$PROJ_DIR/settings_local.py":
        ensure => file,
        source => "$PROJ_DIR/puppet/files/vagrant/settings_local.py";
    }
        
    file { "$PROJ_DIR/kumascript_settings_local.json":
        ensure => file,
        source => "$PROJ_DIR/puppet/files/vagrant/kumascript_settings_local.json";
    }
        
    case $operatingsystem {

        centos: {

            # Sync a yum cache from host machine down to VM
            file { "/etc/yum.conf":
                source => "/vagrant/puppet/files/etc/yum.conf",
                owner => "root", group => "root", mode => 0644;
            }
            file { "/vagrant/puppet/cache/yum":
                ensure => directory
            }
            #exec { "rsync-yum-cache-from-puppet-cache":
            #    command => "/usr/bin/rsync -r /vagrant/puppet/cache/yum/ /var/cache/yum/",
            #    require => [ File["/etc/yum.conf"], File['/vagrant/puppet/cache/yum'] ]
            #}

            file { "/etc/sysconfig/iptables":
                source => "/vagrant/puppet/files/etc/sysconfig/iptables",
                owner => "root", group => "root", mode => 0644;
            }
            exec { "iptables-restart":
                command => '/etc/init.d/iptables restart',
                onlyif => "/usr/bin/test -f /etc/init.d/iptables",
                require => File['/etc/sysconfig/iptables'];
            }

            file { "/etc/sysconfig/network":
                source => "/vagrant/puppet/files/etc/sysconfig/network",
                owner => "root", group => "root", mode => 0644;
            }

            file { "/etc/resolv.conf":
                source => "/vagrant/puppet/files/etc/resolv.conf",
                owner => "root", group => "root", mode => 0644;
            }

            #file { "/etc/samba":
            #    ensure => directory,
            #    recurse => true,
            #    owner => "root", group => "root",
            #    source => "/vagrant/puppet/files/etc/samba"
            #}

            #file { "/etc/issue":
            #    source => "/vagrant/puppet/files/etc/issue",
            #    owner => "root", group => "root", mode => 0644;
            #}

            file { "/etc/motd":
                source => "/vagrant/puppet/files/etc/motd",
                owner => "root", group => "root", mode => 0644;
            }

            #file { "/etc/sudoers":
            #    source => "/vagrant/puppet/files/etc/sudoers",
            #    owner => "root", group => "root", mode => 0440;
            #}
            
            file { "/etc/hosts":
                source => "/vagrant/puppet/files/etc/hosts",
                owner => "root", group => "root", mode => 0644;
            }
            
            # Disable SELinux... causing problems, and I don't understand it.
            # TODO: see http://blog.endpoint.com/2010/02/selinux-httpd-modwsgi-26-rhel-centos-5.html
            file { "/etc/selinux/config":
                source => "/vagrant/puppet/files/etc/selinux/config",
                owner => "root", group => "root", mode => 0644;
            }
            exec { "disable_selinux_enforcement":
                command => "/usr/sbin/setenforce 0",
                unless => "/usr/sbin/getenforce | grep -q 'Disabled'";
            }

        }

    }

}

# Last few things that need doing...
class dev_hacks_post {

    # This bash_profile auto-activates the virtualenv on login, adds some
    # useful things to the $PATH, etc.
    file {
        "/home/vagrant/.bash_profile":
            source => "$PROJ_DIR/puppet/files/home/vagrant/bash_profile",
            owner => "vagrant", group => "vagrant", mode => 0664;
        "/home/vagrant/bin":
            ensure => directory,
            owner => "vagrant", group => "vagrant", mode => 0755;
        "/home/vagrant/bin/go-tmux.sh":
            source => "$PROJ_DIR/puppet/files/home/vagrant/bin/go-tmux.sh",
            owner => "vagrant", group => "vagrant", mode => 0777;
    }
    
    case $operatingsystem {
        centos: {
            # Sync a yum cache up to host machine from VM
            #exec { "rsync-yum-cache-to-puppet-cache":
            #    command => "/usr/bin/rsync -r /var/cache/yum/ /vagrant/puppet/cache/yum/",
            #    require => [ File["/etc/yum.conf"], File['/vagrant/puppet/cache/yum'] ]
            #}
            # Clean up the yum cache, for a smaller box.
            #exec { "purge-local-yum-cache":
            #    command => "/usr/bin/yum clean packages",
            #    require => [ Exec['rsync-yum-cache-to-puppet-cache'] ]
            #}
        }
    }
}
