#
# Configure everything necessary for the site.
#

define apache::loadmodule () {
     exec { "/usr/sbin/a2enmod $name" :
          unless => "/bin/readlink -e /etc/apache2/mods-enabled/${name}.load",
          notify => Service[apache2]
     }
}

class apache_config {
    apache::loadmodule { "env": }
    apache::loadmodule { "setenvif": }
    apache::loadmodule { "headers": }
    apache::loadmodule { "expires": }
    apache::loadmodule { "alias": }
    apache::loadmodule { "rewrite": }
    apache::loadmodule { "proxy": }
    apache::loadmodule { "proxy_http":
        require => Apache::Loadmodule['proxy']
    }
    apache::loadmodule { "vhost_alias": }
    file { "/etc/apache2/ssl":
        ensure => directory, mode => 0644;
    }
    file { "/etc/apache2/ssl/apache.crt":
        source => "/home/vagrant/src/puppet/files/etc/apache2/ssl/apache.crt",
        require => File["/etc/apache2/ssl"],
    }
    file { "/etc/apache2/ssl/apache.key":
        source => "/home/vagrant/src/puppet/files/etc/apache2/ssl/apache.key",
        require => File["/etc/apache2/ssl"],
    }
    apache::loadmodule { "ssl":
        require => [
            File["/etc/apache2/ssl/apache.crt"],
            File["/etc/apache2/ssl/apache.key"],
        ]
    }
    file { "/etc/apache2/conf.d/mozilla-kuma-apache.conf":
        source => "/home/vagrant/src/puppet/files/etc/apache2/conf.d/mozilla-kuma-apache.conf",
        require => [
            Package['apache2'],
            Apache::Loadmodule['env'],
            Apache::Loadmodule['setenvif'],
            Apache::Loadmodule['headers'],
            Apache::Loadmodule['expires'],
            Apache::Loadmodule['alias'],
            Apache::Loadmodule['rewrite'],
            Apache::Loadmodule['ssl'],
            Apache::Loadmodule['proxy'],
            Apache::Loadmodule['proxy_http'],
            Apache::Loadmodule['vhost_alias'],
        ];
    }
    service { "apache2":
        ensure    => running,
        enable    => true,
        require   => [ Package['apache2'], ],
        subscribe => File['/etc/apache2/conf.d/mozilla-kuma-apache.conf']
    }
}

class mysql_config {
    # Ensure MySQL answers on 127.0.0.1, and not just unix socket
    file {
        "/etc/mysql/my.cnf":
            source => "/home/vagrant/src/puppet/files/etc/mysql/my.cnf",
            owner => "root", group => "root", mode => 0644;
        "/tmp/init.sql":
            ensure => file,
            source => "/home/vagrant/src/puppet/files/tmp/init.sql",
            owner => "vagrant", group => "vagrant", mode => 0644;
    }
    service { "mysql":
        ensure => running,
        enable => true,
        require => [ Package['mysql-server'], File["/etc/mysql/my.cnf"] ],
        subscribe => [ File["/etc/mysql/my.cnf"] ]
    }
    exec {
        "setup_mysql_databases_and_users":
            command => "/usr/bin/mysql -u root < /tmp/init.sql",
            unless => "/usr/bin/mysql -uroot -B -e 'show databases' 2>&1 | grep -q 'kuma'",
            require => [
                File["/tmp/init.sql"],
                Service["mysql"]
            ];
    }

}

class rabbitmq_config {
    exec {
        'rabbitmq-kuma-user':
            require => [ Package['rabbitmq-server'], Service['rabbitmq-server'] ],
            command => "/usr/sbin/rabbitmqctl add_user kuma kuma",
            unless => "/usr/sbin/rabbitmqctl list_users 2>&1 | grep -q 'kuma'",
            timeout => 300;
        'rabbitmq-kuma-vhost':
            require => [ Package['rabbitmq-server'], Service['rabbitmq-server'],
                         Exec['rabbitmq-kuma-user'] ],
            command => "/usr/sbin/rabbitmqctl add_vhost kuma",
            unless => "/usr/sbin/rabbitmqctl list_vhosts 2>&1 | grep -q 'kuma'",
            timeout => 300;
        'rabbitmq-kuma-permissions':
            require => [ Package['rabbitmq-server'], Service['rabbitmq-server'],
                         Exec['rabbitmq-kuma-user'], Exec['rabbitmq-kuma-vhost'] ],
            command => "/usr/sbin/rabbitmqctl set_permissions -p kuma kuma '.*' '.*' '.*'",
            unless => "/usr/sbin/rabbitmqctl list_permissions -p kuma 2>&1 | grep -v 'vhost' | grep -q 'kuma'",
            timeout => 300;
    }
}

class kuma_config {
    file {
        "/home/vagrant/src/media/uploads":
            target => "/home/vagrant/uploads",
            ensure => link,
            require => [ File["/home/vagrant/uploads"] ];
        "/home/vagrant/src/webroot/.htaccess":
            ensure => link,
            target => "/home/vagrant/src/configs/htaccess-without-mindtouch";
        "/var/www/.htaccess":
            ensure => link,
            target => "/home/vagrant/src/configs/htaccess-without-mindtouch";
    }
    exec {
        "kuma_update_product_details":
            user => "vagrant",
            cwd => "/home/vagrant/src",
            command => "/home/vagrant/env/bin/python ./manage.py update_product_details",
            timeout => 1200, # Too long, but this can take awhile
            creates => "/home/vagrant/product_details_json/firefox_versions.json",
            require => [
                File["/home/vagrant/product_details_json"]
            ];
        "kuma_sql_migrate":
            user => "vagrant",
            cwd => "/home/vagrant/src",
            command => "/home/vagrant/env/bin/python ./vendor/src/schematic/schematic migrations/",
            require => [ Exec["kuma_update_product_details"],
                Service["mysql"], File["/home/vagrant/logs"] ];
        "kuma_south_migrate":
            user => "vagrant",
            cwd => "/home/vagrant/src",
            command => "/home/vagrant/env/bin/python manage.py migrate",
            require => [ Exec["kuma_sql_migrate"] ];
        "kuma_update_feeds":
            user => "vagrant",
            cwd => "/home/vagrant/src",
            command => "/home/vagrant/env/bin/python ./manage.py update_feeds",
            onlyif => "/usr/bin/mysql -B -uroot kuma -e'select count(*) from feeder_entry' | grep '0'",
            require => [ Exec["kuma_south_migrate"] ];
        "kuma_index_database":
            user => "vagrant",
            cwd => "/home/vagrant/src",
            command => "/home/vagrant/env/bin/python manage.py reindex -p 5",
            timeout => 600,
            require => [ Service["elasticsearch"] ];
    }
}

class site_config {
    include apache_config, mysql_config, rabbitmq_config, kuma_config
    Class[apache_config] -> Class[mysql_config] -> Class[rabbitmq_config] -> Class[kuma_config]
}
