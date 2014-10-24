# Get clean-css
class cleancss {
    exec { 'cleancss-install':
        command => '/usr/bin/npm install -g clean-css@2.2.16',
        creates => '/usr/local/bin/cleancss',
        require => [
            Package['nodejs'],
        ]
    }
    file { '/usr/local/bin/cleancss':
        ensure => link,
        target=> "/usr/bin/cleancss",
        require => Exec['cleancss-install'],
    }
}
