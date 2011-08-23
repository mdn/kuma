# 
# Configure everything necessary for the site.
#

class apache_config {
    file { "/etc/httpd/conf.d/mozilla-kuma-apache.conf":
        source => "$PROJ_DIR/puppet/files/etc/httpd/conf.d/mozilla-kuma-apache.conf",
        owner => "apache", group => "apache", mode => 0644,
        require => [ Package['httpd'] ];
    }
    service { "httpd":
        ensure    => running,
        enable    => true,
        require   => [
            Package['httpd']#,
        ],
        subscribe => File['/etc/httpd/conf.d/mozilla-kuma-apache.conf']
    }
}

class mysql_config {
    # Ensure MySQL answers on 127.0.0.1, and not just unix socket
    file { 
        "/home/vagrant": mode => 0755;
        "/etc/my.cnf":
            source => "$PROJ_DIR/puppet/files/etc/my.cnf",
            owner => "root", group => "root", mode => 0644;
        "/tmp/init.sql":
            ensure => file,
            source => "$PROJ_DIR/puppet/files/tmp/init.sql",
            owner => "vagrant", group => "vagrant", mode => 0644;
        "/tmp/wikidb.sql":
            ensure => file,
            source => "$PROJ_DIR/puppet/files/tmp/wikidb.sql",
            owner => "vagrant", group => "vagrant", mode => 0644;
    }
    service { "mysqld": 
        ensure => running, 
        enable => true, 
        require => [ Package['mysql-server'], File["/etc/my.cnf"] ],
        subscribe => [ File["/etc/my.cnf"] ]
    }
    exec { 
        "setup_mysql_databases_and_users":
            command => "/usr/bin/mysql -u root < /tmp/init.sql",
            unless => "/usr/bin/mysql -uroot -B -e 'show databases' 2>&1 | grep -q 'kuma'",
            require => [ 
                File["/tmp/init.sql"],
                Service["mysqld"] 
            ];
        # HACK: Kind of icky, but I just took a snapshot of a configured deki install
        "setup_mysql_wikidb":
            command => "/usr/bin/mysql -u root wikidb < /tmp/wikidb.sql",
            unless => "/usr/bin/mysql -uroot wikidb -B -e 'show tables' 2>&1 | grep -q 'pages'",
            require => [ 
                File["/tmp/wikidb.sql"],
                Service["mysqld"], 
                Exec["setup_mysql_databases_and_users"] 
            ];
    }
}

class kuma_config {
    file { 
        [ "/home/vagrant/logs",
            "/home/vagrant/uploads",
            "/home/vagrant/product_details_json" ]:
        ensure => directory,
        owner => "vagrant", group => "vagrant", mode => 0777;
    }
    file {
        "/vagrant/media/uploads": 
            target => "/home/vagrant/uploads",
            ensure => link, 
            require => [ File["/home/vagrant/uploads"] ];
    }
    exec { 
        "kuma_update_product_details":
            cwd => "/vagrant", command => "/usr/bin/python2.6 ./manage.py update_product_details",
            creates => "/home/vagrant/product_details_json/firefox_versions.json",
            require => [
                File["/home/vagrant/product_details_json"]
            ];
        "kuma_sql_migrate":
            cwd => "/vagrant", command => "/usr/bin/python2.6 ./vendor/src/schematic/schematic migrations/",
            require => [ Exec["kuma_update_product_details"],
                Service["mysqld"], File["/home/vagrant/logs"] ];
        "kuma_south_migrate":
            cwd => "/vagrant", command => "/usr/bin/python2.6 manage.py migrate",
            require => [ Exec["kuma_sql_migrate"] ];
        "kuma_update_feeds":
            cwd => "/vagrant", command => "/usr/bin/python2.6 ./manage.py update_feeds",
            onlyif => "/usr/bin/mysql -B -uroot kuma -e'select count(*) from feeder_entry' | grep '0'",
            require => [ Exec["kuma_south_migrate"] ];
    }
}

class site_config {
    include apache_config, mysql_config, kuma_config
    Class[apache_config] -> Class[mysql_config] -> Class[kuma_config]
}
