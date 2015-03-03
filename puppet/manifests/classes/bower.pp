class bower {
    exec {'bower-install':
        command => '/usr/bin/npm install -g bower@1.3.12',
        creates => '/usr/bin/bower',
        require => Package['nodejs'],
    }
    file {'/usr/bin/bower':
        require => Exec['bower-install'],
    }

    exec {'bower-run':
        cwd => '/home/vagrant/src/',
        command => '/usr/bin/bower --allow-root --no-interactive install',
        require => [
            File['/usr/bin/bower'],
        ]
    }
}
