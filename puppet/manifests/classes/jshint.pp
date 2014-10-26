# Get stylus
class jshint {
    exec { 'jshint-install':
        command => '/usr/bin/npm install -g jshint@2.15.6',
        creates => '/usr/local/bin/jshint',
        require => [
            Package['nodejs'],
        ]
    }
    file { '/usr/local/bin/jshint':
        require => Exec['jshint-install'],
    }
}
