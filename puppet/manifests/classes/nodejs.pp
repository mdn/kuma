# Get node.js and npm installed Ubuntu 12.04 LTS
class nodejs {
    exec { "nodejs_delete_old_ppa":
        command => "/bin/rm /etc/apt/sources.list.d/chris-lea-node_js-precise.list*",
        onlyif => "/bin/ls -1 /etc/apt/sources.list.d | /bin/grep -c 'chris-lea-node_js-precise.list'"
    }
    exec { "nodejs_uninstall_old_node":
        command => "/usr/bin/apt-get remove -y nodejs",
        onlyif => [
                    "/usr/bin/test -f /usr/bin/node",
                    "/usr/bin/node --version | /bin/grep -c 'v0.6.12'",
                  ]
    }
    exec { "nodejs_download":
        cwd => "/home/vagrant/src/puppet/cache",
        timeout => 300,
        command => "/usr/bin/wget https://s3-us-west-2.amazonaws.com/pkgs.mozilla.net/vagrant/mdn/nodejs_0.10.26-1chl1~precise1_i386.deb",
        creates => "/home/vagrant/src/puppet/cache/nodejs_0.10.26-1chl1~precise1_i386.deb",
    }
    package { "nodejs":
        provider => "dpkg",
        source => "/home/vagrant/src/puppet/cache/nodejs_0.10.26-1chl1~precise1_i386.deb",
        require => [
            Package["rlwrap"],
            Exec['nodejs_download'],
            Exec['nodejs_delete_old_ppa'],
            Exec['nodejs_uninstall_old_node']
        ]
    }
    file { "/usr/include/node":
        target => "/usr/include/nodejs",
        ensure => link,
        require => Package['nodejs']
    }
    file { "/usr/local/lib/node_modules/fibers":
        ensure => absent,
        force => true
    }
    file { "/home/vagrant/src/kumascript/node_modules/fibers":
        ensure => absent,
        force => true
    }
    exec { 'npm-fibers-install':
        command => "/usr/bin/npm install -g fibers@1.0.1",
        creates => "/usr/lib/node_modules/fibers",
        require => [
            Package["nodejs"],
            File["/usr/include/node"],
            File["/usr/local/lib/node_modules/fibers"],
            File["/home/vagrant/src/kumascript/node_modules/fibers"]
        ]
    }
}
