# Ensure some handy dev tools are available.
class dev_tools {
    package { 
        [ "git", "subversion-devel", "mercurial", "vim-enhanced", "man", "man-pages",
            "nfs-utils", "nfs-utils-lib", "telnet", "nc", "rsync" ]:
            ensure => installed;
    }
}

# Do some dirty, dirty things to make development nicer.
class dev_hacks {

    file { "/home/vagrant":
        owner => "vagrant", group => "vagrant", mode => 0755;
    }

    file { "$PROJ_DIR/settings_local.py":
        ensure => file,
        source => "$PROJ_DIR/puppet/files/vagrant/settings_local.py";
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
            exec { "rsync-yum-cache-from-puppet-cache":
                command => "/usr/bin/rsync -r /vagrant/puppet/cache/yum/ /var/cache/yum/",
                require => [ File["/etc/yum.conf"], File['/vagrant/puppet/cache/yum'] ]
            }

            file { "/etc/sysconfig/iptables":
                source => "/vagrant/puppet/files/etc/sysconfig/iptables",
                owner => "root", group => "root", mode => 0644;
            }
            exec { "iptables-restart":
                command => '/etc/init.d/iptables restart',
                onlyif => "/usr/bin/test -f /etc/init.d/iptables",
                require => File['/etc/sysconfig/iptables'];
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
    case $operatingsystem {
        centos: {
            # Sync a yum cache up to host machine from VM
            exec { "rsync-yum-cache-to-puppet-cache":
                command => "/usr/bin/rsync -r /var/cache/yum/ /vagrant/puppet/cache/yum/",
                require => [ File["/etc/yum.conf"], File['/vagrant/puppet/cache/yum'] ]
            }
        }
    }
}
