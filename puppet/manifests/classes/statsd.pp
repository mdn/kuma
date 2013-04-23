# see also: http://www.kinvey.com/blog/89/how-to-set-up-metric-collection-using-graphite-and-statsd-on-ubuntu-1204-lts
class statsd {
    exec { 'statsd-install':
        cwd => '/home/vagrant',
        user => 'vagrant',
        # TODO: This revision works, but try to see what statsd runs in mozilla infra
        command => '/usr/bin/npm install git://github.com/etsy/statsd.git#922e9e58c57ae4e61268cbd6925c112f0e4e468c',
        creates => '/home/vagrant/node_modules/statsd',
        require => [Package["nodejs"], Package["npm"]]
    }
    file { '/home/vagrant/statsd-config.js':
        source => '/vagrant/puppet/files/home/vagrant/statsd-config.js',
        owner => "vagrant", group => "vagrant", mode => 0664,
        require => Exec['statsd-install']
    }
    package {
        ['sqlite3', 'libcairo2', 'libcairo2-dev', 'python-cairo', 'pkg-config']:
        ensure => present;
    }
    exec { 'graphite-install':
         cwd => '/tmp',
         timeout => 1200, # Too long, but this can take awhile
         command => '/usr/bin/pip install --download-cache=/vagrant/puppet/cache/pip -r /vagrant/puppet/files/tmp/graphite_reqs.txt',
         creates => '/opt/graphite/webapp/graphite/manage.py';
    }
    file { '/opt/graphite/conf/carbon.conf':
        source => '/opt/graphite/conf/carbon.conf.example',
        owner => "root", group => "www-data", mode => 0664,
        require => Exec['graphite-install']
    }
    file { '/opt/graphite/webapp/graphite/local_settings.py':
        source => '/opt/graphite/webapp/graphite/local_settings.py.example',
        owner => "root", group => "www-data", mode => 0664,
        require => Exec['graphite-install']
    }
    file { '/opt/graphite/conf/graphite.wsgi':
        source => '/opt/graphite/conf/graphite.wsgi.example',
        owner => "root", group => "www-data", mode => 0664,
        require => Exec['graphite-install']
    }
    file { '/opt/graphite/storage/log/webapp':
        ensure => directory,
        owner => "www-data", group => "www-data", mode => 0775,
        require => Exec['graphite-install']
    }
    file { '/opt/graphite/conf/storage-schemas.conf':
        source => '/vagrant/puppet/files/opt/graphite/conf/storage-schemas.conf',
        owner => "root", group => "www-data", mode => 0664,
        require => Exec['graphite-install']
    }
    file { '/etc/init/statsd.conf':
        source => '/vagrant/puppet/files/etc/init/statsd.conf',
        owner => "root", group => "www-data", mode => 0775,
        require => Exec['statsd-install']
    }
    file { '/etc/init/carbon-cache.conf':
        source => '/vagrant/puppet/files/etc/init/carbon-cache.conf',
        owner => "root", group => "www-data", mode => 0775,
        require => Exec['graphite-install']
    }
    exec { 'graphite-syncdb':
        cwd => '/opt/graphite/webapp/graphite',
        command => '/usr/bin/python manage.py syncdb --noinput',
        creates => '/opt/graphite/storage/graphite.db',
        require => Exec['graphite-install']
    }
    exec { 'graphite-superuser':
        cwd => '/opt/graphite/webapp/graphite',
        command => '/usr/bin/python manage.py loaddata /vagrant/puppet/files/tmp/graphite_auth.json',
        unless => "/usr/bin/sqlite3 /opt/graphite/storage/graphite.db 'select * from auth_user' | /bin/grep -q admin",
        require => Exec['graphite-syncdb']
    }
    service { 'carbon-cache':
        ensure => running,
        enable => true,
        require => File['/etc/init/carbon-cache.conf']
    }
    service { 'statsd':
        ensure => running,
        enable => true,
        require => File['/etc/init/statsd.conf']
    }
        
}
