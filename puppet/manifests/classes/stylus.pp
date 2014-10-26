# Get stylus
class stylus {
    exec { 'stylus-install':
        command => '/usr/bin/npm install -g stylus@0.43.1',
        creates => '/usr/bin/stylus',
        require => [
            Package['nodejs'],
        ]
    }
    file { '/usr/local/bin/stylus':
        ensure => link,
        target=> "/usr/bin/stylus",
        require => Exec['stylus-install'],
    }
}
