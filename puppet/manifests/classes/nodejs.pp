# Get node.js and npm installed Ubuntu 12.04 LTS
class nodejs {
    # See also: https://launchpad.net/~chris-lea/+archive/node.js/
    exec { 'install-chris-lea-node-repo':
        command => '/usr/bin/apt-add-repository -y ppa:chris-lea/node.js && /usr/bin/apt-get update',
        creates => '/etc/apt/sources.list.d/chris-lea-node_js-precise.list',
        require => Package['python-software-properties']
    }
    package { 'nodejs':
        ensure => '0.10.26-1chl1~precise1',
        require => Exec['install-chris-lea-node-repo']
    }
    file { "/usr/include/node":
        target => "/usr/include/nodejs",
        ensure => link,
        require => Package['nodejs']
    }
    exec { 'npm-fibers-install':
        command => "/usr/bin/npm install -g fibers@1.0.1",
        creates => "/usr/lib/node_modules/fibers",
        require => [
            Package["nodejs"],
            File["/usr/include/node"]
        ]
    }
    # An old version of fibers lived here, ensure it's gone.
    file { "/usr/local/lib/node_modules/fibers":
        ensure => absent,
        force => true
    }
}
