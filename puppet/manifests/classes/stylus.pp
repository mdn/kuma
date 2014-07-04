# Get stylus
class stylus {
    exec { 'stylus-install':
        command => '/usr/bin/npm install -g stylus@0.43.1',
        creates => '/usr/local/bin/stylus',
        require => [
            Package['nodejs'],
        ]
    }
    file { '/usr/local/bin/stylus':
        require => Exec['stylus-install'],
    }
}
