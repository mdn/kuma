class cssmin {
    exec { 'cssmin-install':
        command => '/usr/bin/npm install -g cssmin@0.4.3',
        creates => '/usr/local/bin/cssmin',
        require => [
            Package['nodejs'],
        ]
    }
    file { '/usr/local/bin/cssmin':
        require => Exec['cssmin-install'],
    }
}
