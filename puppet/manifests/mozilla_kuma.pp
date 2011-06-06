# TODO:
#
#   * NFS isn't installed in the centos box I've been using, so nfs can't be
#       enabled in vagrant at first
# 
#   * even with NFS, the Django app can be very slow over shared folder - make
#       a local copy and regularly rsync?
#
#   * selinux in enforced mode seems to be causing 403 Forbidden errors - why?
#
#   * don't have the right mod_rewrite rules & etc to get deki and kuma working
#
#   * sometimes need to re-run sudo puppet apply
#       /vagrant/puppet/manifests/mozilla_kuma.pp after initial vagrant up
#

group { 
    "admin": ensure => present, gid => "501";
    "vagrant": ensure => present, gid => "502";
}
user { 
    "vagrant": ensure => present, uid => "502", gid => ["admin","vagrant"] 
}

# see also: http://developer.mindtouch.com/en/docs/mindtouch_setup/010Installation/060Installing_on_CentOS
exec { 
    "repo_epel":
        command => "/bin/rpm -Uvh http://download.fedora.redhat.com/pub/epel/5/x86_64/epel-release-5-4.noarch.rpm",
        creates => '/etc/yum.repos.d/epel.repo';
}

file { 
    # see also: http://developer.mindtouch.com/en/docs/mindtouch_setup/010Installation/060Installing_on_CentOS/Installing%2F%2FUpgrade_Mono_on_CentOS
    "repo_mono":
        path => "/etc/yum.repos.d/mono.repo",
        ensure => file,
        source => "/vagrant/puppet/files/etc/yum.repos.d/mono.repo",
        owner => "root", group => "root", mode => 0644;
    "repo_mindtouch":
        path => "/etc/yum.repos.d/mindtouch.repo",
        ensure => file,
        source => "/vagrant/puppet/files/etc/yum.repos.d/mindtouch.repo",
        owner => "root", group => "root", mode => 0644;
}

package { 

    [ "man", "man-pages", "vim-enhanced", "httpd-devel", "mysql-devel",
        "openssl-devel", "nfs-utils", "nfs-utils-lib", "mysql-server", "php-mysql",
        "vixie-cron"]: 
        ensure => installed;

    [ "tidy", "git", "wv", "subversion-devel", "cabextract", "html2ps",
        "html2text", "memcached-devel", "libxml2", "libxml2-devel", "libxslt",
        "libxslt-devel", "libjpeg", "libjpeg-devel", "libpng", "libpng-devel",
        "python26-devel", "python26-libs", "python26-distribute",
        "python26-mod_wsgi", "python26-jinja2", "python26-imaging",
        "python26-imaging-devel", "python-lxml" ]:
        ensure => installed, require => Exec['repo_epel']; 

}

# HACK: Would this be better as a standalone script?
exec { 
    "princexml_download":
        cwd => '/tmp', 
        command => "/usr/bin/wget http://www.princexml.com/download/prince-7.1-linux.tar.gz",
        creates => '/tmp/prince-7.1-linux.tar.gz';
    "princexml_unpack":
        cwd => '/tmp', 
        command => "/bin/tar xfzv prince-7.1-linux.tar.gz",
        creates => '/tmp/prince-7.1-linux',
        require => Exec['princexml_download'];
    "princexml_install":
        cwd => "/tmp/prince-7.1-linux", 
        command => "/tmp/prince-7.1-linux/install.sh",
        creates => "/usr/local/bin/prince", 
        require => Exec['princexml_unpack'];
}

# see also: http://developer.mindtouch.com/en/docs/mindtouch_setup/010Installation/060Installing_on_CentOS/Installing%2F%2FUpgrade_Mono_on_CentOS
package { 
    ["mono-addon-core", "mono-addon-data", "mono-addon-web",
        "mono-addon-winforms", "mono-addon-wcf", "mono-addon-libgdiplus0",
        "mono-addon-data-sqlite", "mono-addon-extras"]: 
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

package {
    "mindtouch": ensure => installed, 
        require => [ 
            Package['mono-addon-core'], 
            File['repo_mindtouch'], 
            Exec['princexml_install'] 
        ];
}

# HACK: Is there a provider for this?
exec { "pip-install": 
    command => "/usr/bin/easy_install-2.6 -U pip", 
    creates => "/usr/bin/pip",
    require => Package["python26-devel","python26-distribute"]
}

# HACK: Might be better if there were RPMs for these, or define a resource type.
exec { 
    "mysql-python-install":
        command => "/usr/bin/pip install mysql-python",
        creates => "/usr/lib/python2.6/site-packages/MySQLdb/__init__.py",
        require => [ Exec["pip-install"], Package["mysql-devel"] ];
    "lxml-install":
        command => "/usr/bin/pip install lxml",
        creates => "/usr/lib/python2.6/site-packages/lxml/__init__.py",
        require => [ Exec["pip-install"], Package["libxml2-devel", "libxslt-devel"] ];
    "django-devserver":
        command => "/usr/bin/pip install django-devserver",
        creates => "/usr/lib/python2.6/site-packages/devserver/__init__.py",
        require => [ Exec["pip-install"] ];
    "django-extensions":
        command => "/usr/bin/pip install django-extensions",
        creates => "/usr/lib/python2.6/site-packages/django_extensions/__init__.py",
        require => [ Exec["pip-install"] ];
    "django-debug-toolbar":
        command => "/usr/bin/pip install -e git://github.com/robhudson/django-debug-toolbar.git#egg=django_debug_toolbar",
        creates => "/usr/lib/python2.6/site-packages/django-debug-toolbar.egg-link",
        require => [ Exec["pip-install"] ];
}

file { 
    
    [ "/home/vagrant", 
        "/home/vagrant/logs",
        "/home/vagrant/uploads",
        "/home/vagrant/product_details_json",
        "/home/vagrant/mdc_pages"]:
        ensure => directory,
        owner => "vagrant", group => "vagrant", mode => 0755;
    
    "/vagrant/settings_local.py":
        ensure => file,
        source => "/vagrant/puppet/files/vagrant/settings_local.py";

    "/tmp/init.sql":
        ensure => file,
        source => "/vagrant/puppet/files/tmp/init.sql",
        owner => "vagrant", group => "vagrant", mode => 0644;

    "/tmp/wikidb.sql":
        ensure => file,
        source => "/vagrant/puppet/files/tmp/wikidb.sql",
        owner => "vagrant", group => "vagrant", mode => 0644;

    # Licence activation file for Open Source mindtouch version
    "/tmp/mindtouch-core.xml":
        ensure => file,
        source => "/vagrant/puppet/files/tmp/mindtouch-core.xml",
        owner => "vagrant", group => "vagrant", mode => 0644;
    
    "/etc/httpd/conf.d/mozilla-kuma-apache.conf":
        source => "/vagrant/puppet/files/etc/httpd/conf.d/mozilla-kuma-apache.conf",
        owner => "dekiwiki", group => "apache", mode => 0644,
        require => [ Package['httpd-devel'], Package["mysql-server"], Package["mindtouch"] ];
    
    # HACK: Disable SELinux... causing problems, and I don't understand it.
    # TODO: see http://blog.endpoint.com/2010/02/selinux-httpd-modwsgi-26-rhel-centos-5.html
    "/etc/selinux/config":
        source => "/vagrant/puppet/files/etc/selinux/config",
        owner => "root", group => "root", mode => 0644;
    
    # Ensure port 80 and 8000 are open for connections.
    #"/etc/sysconfig/iptables":
    #    source => "/vagrant/puppet/files/etc/sysconfig/iptables",
    #    owner => "root", group => "root", mode => 0600;
    
    # Ensure MySQL answers on 127.0.0.1, and not just unix socket
    "/etc/my.cnf":
        source => "/vagrant/puppet/files/etc/my.cnf",
        owner => "root", group => "root", mode => 0644;
    
    "/etc/dekiwiki":
        ensure => directory,
        owner => "root", group => "root", mode => 0755,
        require => [ Package['httpd-devel'], Package["mysql-server"], Package["mindtouch"] ];
    "/etc/dekiwiki/mindtouch.deki.startup.xml":
        ensure => file,
        source => "/vagrant/puppet/files/etc/dekiwiki/mindtouch.deki.startup.xml",
        owner => "apache", group => "apache", mode => 0644,
        require => [ Package['httpd-devel'], Package["mysql-server"], Package["mindtouch"] ];
    "/etc/dekiwiki/mindtouch.host.conf":
        ensure => file,
        source => "/vagrant/puppet/files/etc/dekiwiki/mindtouch.host.conf",
        owner => "apache", group => "apache", mode => 0644,
        require => [ Package['httpd-devel'], Package["mysql-server"], Package["mindtouch"] ];

    "/var/www/dekiwiki/.htaccess":
        ensure => link,
        target => "/vagrant/configs/htaccess",
        require => Package["mindtouch"],
        owner => "apache", group => "apache", mode => 0644;
    "/var/www/dekiwiki/favicon.ico":
        ensure => file,
        source => "/vagrant/puppet/files/var/www/dekiwiki/favicon.ico",
        require => Package["mindtouch"],
        owner => "apache", group => "apache", mode => 0644;
    "/var/www/dekiwiki/LocalSettings.php":
        ensure => file,
        source => "/vagrant/puppet/files/var/www/dekiwiki/LocalSettings.php",
        require => Package["mindtouch"],
        owner => "apache", group => "apache", mode => 0644;
    "/var/www/dekiwiki/skins/mozilla/": 
        target => "/home/vagrant/mozilla/skins/mozilla/",
        ensure => link, require => [ Exec["svn_co_deki_mozilla"], Package["mindtouch"] ];
    "/var/www/dekiwiki/skins/mdn/": 
        target => "/home/vagrant/mozilla/skins/mdn/",
        ensure => link, require => [ Exec["svn_co_deki_mozilla"], Package["mindtouch"] ];
    "/var/www/dekiwiki/deki/plugins/special_page/special_tagrename/": 
        target => "/home/vagrant/mozilla/plugins/mindtouch/special_tagrename/",
        ensure => link, require => [ Exec["svn_co_deki_mozilla"], Package["mindtouch"] ];
    "/var/www/dekiwiki/deki/plugins/special_page/special_userregistration_mdc/": 
        target => "/home/vagrant/mozilla/plugins/mindtouch/special_userregistration_mdc/",
        ensure => link, require => [ Exec["svn_co_deki_mozilla"], Package["mindtouch"] ];
    "/var/www/dekiwiki/editor/fckeditor/core/editor/plugins/mdc/": 
        target => "/home/vagrant/mozilla/plugins/fckeditor/mdc/",
        ensure => link, require => [ Exec["svn_co_deki_mozilla"], Package["mindtouch"] ];

    #"/usr/bin/python":
    #    target => "/usr/bin/python2.6",
    #    ensure => link,
    #    require => Package['python26-devel'];
}

service { 
    "httpd": 
        ensure => running, 
        enable => true, 
        require => Package['httpd-devel'],
        subscribe => [ 
            #Service['iptables'], 
            File["/etc/httpd/conf.d/mozilla-kuma-apache.conf"],
            File["/vagrant/settings_local.py"],
            File["/home/vagrant/logs"]
        ];
    "mysqld": 
        ensure => running, 
        enable => true, 
        require => Package['mysql-server'],
        subscribe => File["/etc/my.cnf"];
    "dekiwiki":
        ensure => running,
        enable => true,
        require => [ 
            Service['httpd'], 
            Service['mysqld'], 
            Package['mindtouch'] 
        ],
        subscribe => [ 
            File["/etc/dekiwiki/mindtouch.host.conf"], 
            File["/etc/dekiwiki/mindtouch.deki.startup.xml"] 
        ];
    #"iptables": 
    #    ensure => running, 
    #    enable => true, 
    #    hasrestart => true, 
    #    hasstatus => true,
    #    subscribe  => File["/etc/sysconfig/iptables"];
}

exec { 
    "vendor_lib_git_submodule_update":
        command => "/usr/bin/git submodule update --init --recursive",
        cwd => "/vagrant",
        creates => "/vagrant/vendor/src/django/README";
    "svn_co_deki_mozilla":
        command => "/usr/bin/svn co http://svn.mozilla.org/projects/deki/trunk/mozilla/",
        cwd => "/home/vagrant",
        creates => "/home/vagrant/mozilla",
        require => [ Package['mindtouch'], Package['subversion-devel'] ];
    "link_dekiwiki_resources":
        command => "/bin/ln -s /home/vagrant/mozilla/resources/resources.custom*.txt /var/www/dekiwiki/resources/",
        creates => "/var/www/dekiwiki/resources/resources.custom.de.txt",
        require => [ Exec["svn_co_deki_mozilla"], Package["mindtouch"] ];
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
    # Not sure I like this, but I can't find where the license is stored to
    # restore a file or whatnot.
    "mindtouch_product_activation":
        command => '/usr/bin/curl -u admin:admin -H "Expect:" -H "Content-Type: application/xml" -T /tmp/mindtouch-core.xml -i http://localhost/@api/deki/license',
        onlyif => "/usr/bin/curl -s 'http://localhost/@api/deki/license' | grep -q 'inactive'",
        require => [
            Package["mindtouch"], Service["httpd"], Service["dekiwiki"],
            File["/tmp/mindtouch-core.xml"],
            File["/etc/dekiwiki/mindtouch.host.conf"], 
            File["/etc/dekiwiki/mindtouch.deki.startup.xml"],
            Exec["setup_mysql_wikidb"]
        ];
    "kuma_sql_migrate":
        cwd => "/vagrant", command => "/usr/bin/python2.6 ./vendor/src/schematic/schematic migrations/",
        require => [
            Service["mysqld"],
            Package["python26-devel", "python26-mod_wsgi", "python26-jinja2",
                "python26-imaging"],
            Exec["mysql-python-install", "lxml-install",
                "setup_mysql_databases_and_users",
                "vendor_lib_git_submodule_update"]
        ];
    "kuma_south_migrate":
        cwd => "/vagrant", command => "/usr/bin/python2.6 manage.py migrate",
        require => [
            Exec["kuma_sql_migrate"]
        ];

    #
    # These commands work, but I haven't figured out conditions to check to
    # keep them from running repeatedly after initial setup.
    #
    "kuma_update_product_details":
        cwd => "/vagrant", command => "/usr/bin/python2.6 ./manage.py update_product_details",
        require => [
            Exec["kuma_south_migrate"],
            File["/home/vagrant/product_details_json"]
        ];
    "kuma_update_feeds":
        cwd => "/vagrant", command => "/usr/bin/python2.6 ./manage.py update_feeds",
        require => [
            Exec["kuma_south_migrate"]
        ];

    # HACK: Disable SELinux... causing problems, and I don't understand it.
    # TODO: see http://blog.endpoint.com/2010/02/selinux-httpd-modwsgi-26-rhel-centos-5.html
    "disable_selinux_enforcement":
        command => "/usr/sbin/setenforce 0",
        unless => "/usr/sbin/getenforce | grep -q 'Disabled'";
}

# selboolean { 
#    "httpd_can_network_connect": value => on, persistent => true;
#    "httpd_read_user_content": value => on, persistent => true;
#    "httpd_use_nfs": value => on, persistent => true;
# }
