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
    file { "/usr/share/npm/npmrc":
        ensure => file,
        owner => "root", group => "root", mode => 0755,
        source => "/home/vagrant/src/puppet/files/usr/share/npm/npmrc",
        require => Package["npm"]
    }
    exec { 'npm-fibers-install':
        command => "/usr/bin/npm install -g fibers@0.6.4",
        creates => "/usr/local/lib/node_modules/fibers",
        require => [
            Package["nodejs"], Package["nodejs-dev"], Package["npm"],
            File["/usr/include/node"], File["/root/.npm"],
            File["/usr/share/npm/npmrc"]
        ]
    }
}
