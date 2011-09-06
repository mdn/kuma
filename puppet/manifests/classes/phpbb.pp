# Basic installation of phpBB
class phpbb {
    # HACK: Would this be better as a standalone script?
    exec {
        "phpbb_download":
            cwd => "$PROJ_DIR/puppet/cache", 
            command => "/usr/bin/wget http://www.phpbb.com/files/archive/3.0.7-PL1/phpBB-3.0.7-PL1.tar.bz2",
            creates => "$PROJ_DIR/puppet/cache/phpBB-3.0.7-PL1.tar.bz2";
        "phpbb_install": 
            command => "/bin/tar -xjf $PROJ_DIR/puppet/cache/phpBB-3.0.7-PL1.tar.bz2 && mv phpBB3 /var/www/forums",
            creates => "/var/www/forums/index.php",
            require => [Exec['phpbb_download']];
    }
}

# Configure phpBB installation for MDN specifics
class phpbb_config {

    file { 
        "/var/www/forums/config.php":
            ensure => file,
            owner => "apache", group => "apache", mode => 0777,
            require => [ Package['httpd-devel'] ];
        "/var/www/forums/store":
            ensure => directory,
            owner => "apache", group => "apache", mode => 0777,
            require => [ Package['httpd-devel'] ];
        "/var/www/forums/cache":
            ensure => directory,
            owner => "apache", group => "apache", mode => 0777,
            require => [ Package['httpd-devel'] ];
        "/var/www/forums/files":
            ensure => directory,
            owner => "apache", group => "apache", mode => 0777,
            require => [ Package['httpd-devel'] ];
        "/var/www/forums/images/avatars/upload":
            ensure => directory,
            owner => "apache", group => "apache", mode => 0777,
            require => [ Package['httpd-devel'] ];
    }

    exec {
        "svn_co_phpbb_mozilla":
            command => "/usr/bin/svn co http://svn.mozilla.org/projects/mdn/trunk/phpbb",
            cwd => "/home/vagrant",
            creates => "/home/vagrant/phpbb",
            require => [ Exec['phpbb_install'], Package['subversion-devel'] ];
        "cp_auth_mdc":
            command => "/bin/cp auth_mdc.php /var/www/forums/includes/auth/auth_mdc.php",
            cwd => "/home/vagrant/phpbb",
            creates => "/var/www/forums/includes/auth/auth_mdc.php",
            require => [ Exec['svn_co_phpbb_mozilla'] ];
        "cp_functions":
            command => "/bin/cp includes/functions.php /var/www/forums/includes/functions.php",
            cwd => "/home/vagrant/phpbb",
            creates => "/var/www/forums/includes/functions.php",
            require => [ Exec['svn_co_phpbb_mozilla'] ];
        "cp_viewforum":
            command => "/bin/cp viewforum.php /var/www/forums/viewforum.php",
            cwd => "/home/vagrant/phpbb",
            creates => "/var/www/forums/viewforum.php",
            require => [ Exec['svn_co_phpbb_mozilla'] ];
        "cp_viewtopic":
            command => "/bin/cp viewtopic.php /var/www/forums/viewtopic.php",
            cwd => "/home/vagrant/phpbb",
            creates => "/var/www/forums/viewtopic.php",
            require => [ Exec['svn_co_phpbb_mozilla'] ];
        "cp_styles":
            command => "/bin/cp -R styles/MDN /var/www/forums/styles/MDN",
            cwd => "/home/vagrant/phpbb",
            creates => "/var/www/forums/styles/MDN",
            require => [ Exec['svn_co_phpbb_mozilla'] ];
    }
}
