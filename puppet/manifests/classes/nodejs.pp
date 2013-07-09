# Get node.js and npm installed under CentOS
class nodejs {
    package {
        [ "nodejs", "nodejs-dev", "npm" ]:
            ensure => installed;
    }
    file { "/usr/include/node":
        target => "/usr/include/nodejs",
        ensure => link,
        require => Package['nodejs-dev']
    }
    exec { 'npm-install':
        cwd => "/vagrant/kumascript",
        command => "/usr/bin/npm install",
        creates => "/vagrant/kumascript/node_modules/fibers",
        require => [
            Package["nodejs"], Package["nodejs-dev"], Package["npm"],
            File["/usr/include/node"],
        ]
    }
}
