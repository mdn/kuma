class cssmin {
    exec { 'cssmin-install':
        command => '/usr/bin/npm install -g cssmin@0.4.3',
        creates => '/usr/bin/cssmin',
        require => [
            Package['nodejs'],
        ]
    }
    file { '/usr/bin/cssmin':
        ensure => file,
        target=> "/usr/bin/cssmin",
        require => Exec['cssmin-install'],
    }
}
