# Basic installation of Mindtouch / Dekiwiki
class dekiwiki {

    package {
        [ "tidy", "wv", "cabextract", "html2ps", "html2text", "unzip" ]:
            ensure => installed, require => Exec["repo_epel"]; 
    }

    # see also: http://developer.mindtouch.com/en/docs/mindtouch_setup/010Installation/060Installing_on_CentOS/Installing%2F%2FUpgrade_Mono_on_CentOS
    package { 
        ["mono-addon-core", "mono-addon-data", "mono-addon-web",
            "mono-addon-winforms", "mono-addon-wcf", "mono-addon-libgdiplus0",
            "mono-addon-data-sqlite", "mono-addon-extras" ]: 
            ensure => installed, require => File['repo_mono'];
    }

    file {
        "/usr/bin/mono": 
            ensure => link, target => "/opt/novell/mono/bin/mono",
            require => Package["mono-addon-core"];
        "/usr/bin/gmcs": 
            ensure => link, target => "/opt/novell/mono/bin/gmcs",
            require => Package["mono-addon-core"];
    }

    # HACK: Would this be better as a standalone script?
    exec { 
        "princexml_download":
            cwd => "$PROJ_DIR/puppet/cache", 
            command => "/usr/bin/wget http://www.princexml.com/download/prince-7.1-linux.tar.gz",
            creates => "$PROJ_DIR/puppet/cache/prince-7.1-linux.tar.gz";
        "princexml_unpack":
            cwd => "$PROJ_DIR/puppet/cache", 
            command => "/bin/tar xfzv prince-7.1-linux.tar.gz",
            creates => "$PROJ_DIR/puppet/cache/prince-7.1-linux",
            require => Exec['princexml_download'];
        "princexml_install":
            cwd => "$PROJ_DIR/puppet/cache/prince-7.1-linux", 
            command => "$PROJ_DIR/puppet/cache/prince-7.1-linux/install.sh",
            creates => "/usr/local/bin/prince", 
            require => Exec['princexml_unpack'];
    }

    # This is the older version of Mindtouch we were using
    #exec {
    #    "mindtouch_download":
    #        cwd => "$PROJ_DIR/puppet/cache", 
    #        command => "/usr/bin/wget http://repo.mindtouch.com/CentOS_5/noarch/dekiwiki-9.12.3-1.2.noarch.rpm",
    #        creates => "$PROJ_DIR/puppet/cache/dekiwiki-9.12.3-1.2.noarch.rpm";
    #    "mindtouch_install": 
    #        command => "/bin/rpm -Uvh $PROJ_DIR/puppet/cache/dekiwiki-9.12.3-1.2.noarch.rpm",
    #        creates => "/var/www/dekiwiki/index.php",
    #        require => [ Exec['princexml_install'], Exec['mindtouch_download'] ];
    #}

    # Installs v10, for which we're not yet ready without a lengthy database migration
    package {
        "mindtouch": ensure => installed, 
            require => [ 
                Package['mono-addon-core'], 
                File['repo_mindtouch'], 
                Exec['princexml_install'] 
            ];
    }
    
}

# Configure dekiwiki installation for MDN specifics
class dekiwiki_config {

    file { 
        # Licence activation file for Open Source mindtouch version
        "/tmp/mindtouch-core.xml":
            ensure => file,
            source => "$PROJ_DIR/puppet/files/tmp/mindtouch-core.xml",
            owner => "vagrant", group => "vagrant", mode => 0644;
        "/etc/dekiwiki":
            ensure => directory,
            owner => "dekiwiki", group => "apache", mode => 0750,
            require => [ Package['httpd-devel'], Package["mysql-server"] ];
        "/etc/dekiwiki/mindtouch.deki.startup.xml":
            ensure => file,
            source => "$PROJ_DIR/puppet/files/etc/dekiwiki/mindtouch.deki.startup.xml",
            owner => "apache", group => "apache", mode => 0644,
            require => [ Package['httpd-devel'], Package["mysql-server"] ];
        "/etc/dekiwiki/mindtouch.host.conf":
            ensure => file,
            source => "$PROJ_DIR/puppet/files/etc/dekiwiki/mindtouch.host.conf",
            owner => "apache", group => "apache", mode => 0644,
            require => [ Package['httpd-devel'], Package["mysql-server"] ];
        "/var/www/dekiwiki/.htaccess":
            ensure => link,
            target => "$PROJ_DIR/configs/htaccess",
            owner => "apache", group => "apache", mode => 0644;
        "/var/www/dekiwiki/favicon.ico":
            ensure => file,
            source => "$PROJ_DIR/puppet/files/var/www/dekiwiki/favicon.ico",
            owner => "apache", group => "apache", mode => 0644;
        "/var/www/dekiwiki/LocalSettings.php":
            ensure => file,
            source => "$PROJ_DIR/puppet/files/var/www/dekiwiki/LocalSettings.php",
            owner => "apache", group => "apache", mode => 0644;
        "/var/www/dekiwiki/skins/mozilla/": 
            target => "/home/vagrant/mozilla/skins/mozilla/",
            ensure => link, require => [ Exec["svn_co_deki_mozilla"] ];
        "/var/www/dekiwiki/skins/mdn/": 
            target => "/home/vagrant/mozilla/skins/mdn/",
            ensure => link, require => [ Exec["svn_co_deki_mozilla"] ];
        "/var/www/dekiwiki/deki/plugins/special_page/special_tagrename/": 
            target => "/home/vagrant/mozilla/plugins/mindtouch/special_tagrename/",
            ensure => link, require => [ Exec["svn_co_deki_mozilla"] ];
        "/var/www/dekiwiki/deki/plugins/special_page/special_userregistration_mdc/": 
            target => "/home/vagrant/mozilla/plugins/mindtouch/special_userregistration_mdc/",
            ensure => link, require => [ Exec["svn_co_deki_mozilla"] ];
    }

    service { "dekiwiki":
        ensure => running,
        enable => true,
        require => [ Service['httpd'], Service['mysqld'] ],
        subscribe => [ 
            File["/etc/dekiwiki/mindtouch.host.conf"], 
            File["/etc/dekiwiki/mindtouch.deki.startup.xml"] 
        ];
    }

    exec { 
        "svn_co_deki_mozilla":
            command => "/usr/bin/svn co http://svn.mozilla.org/projects/deki/trunk/mozilla/",
            cwd => "/home/vagrant",
            creates => "/home/vagrant/mozilla",
            require => [ Package['mindtouch'] ];
        # Ensure the deki SVN assets are kept up to date
        "svn_up_deki_mozilla":
            command => "/usr/bin/svn up",
            cwd => "/home/vagrant/mozilla",
            require => [ Exec["svn_co_deki_mozilla"] ];
        "link_dekiwiki_resources":
            command => "/bin/ln -s /home/vagrant/mozilla/resources/resources.custom*.txt /var/www/dekiwiki/resources/",
            creates => "/var/www/dekiwiki/resources/resources.custom.de.txt",
            require => [ Exec["svn_co_deki_mozilla"] ];
        # Not sure I like this, but I can't find where the license is stored to
        # restore a file or whatnot.
        "mindtouch_product_activation":
            command => '/usr/bin/curl -u admin:admin -H "Expect:" -H "Content-Type: application/xml" -T /tmp/mindtouch-core.xml -i http://localhost/@api/deki/license',
            onlyif => "/usr/bin/curl -s 'http://localhost/@api/deki/license' | grep -q 'inactive'",
            require => [
                Service["httpd"], Service["dekiwiki"],
                File["/tmp/mindtouch-core.xml"],
                File["/etc/dekiwiki/mindtouch.host.conf"], 
                File["/etc/dekiwiki/mindtouch.deki.startup.xml"],
                Exec["setup_mysql_wikidb"]
            ];
    }

}
