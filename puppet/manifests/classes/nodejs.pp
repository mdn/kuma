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

    # HACK: npm seems to have a bug in this environment where it believes the
    # active user is still root, even when it's  vagrant. So, it tries to
    # access /root/.npm, which throws a file permission error. This dirty dirty
    # hack applies a bandaid in exchange for exposing /root slightly
    file { "/root":
        ensure => directory,
        owner => "root", group => "root", mode => 0666;
    }
    file { "/root/.npm":
        ensure => directory,
        owner => "root", group => "root", mode => 0777,
        require => File["/root"];
    }
    
    exec { 'npm-install':
        cwd => "/vagrant/kumascript",
        user => 'vagrant',
        command => "/usr/bin/npm install fibers",
        creates => "/vagrant/kumascript/node_modules/fibers",
        require => [
            Package["nodejs"], Package["nodejs-dev"], Package["npm"],
            File["/usr/include/node"], File["/root/.npm"]
        ]
    }
}
