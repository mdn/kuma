# Get stylus
class csslint {
    exec { 'csslint-install':
        command => '/usr/bin/npm install -g csslint@0.10.0',
        creates => '/usr/local/bin/csslint',
        require => [
            Package['nodejs'],
        ]
    }
    file { '/usr/local/bin/csslint':
        require => Exec['csslint-install'],
    }
}
