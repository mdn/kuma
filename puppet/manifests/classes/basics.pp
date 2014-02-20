class basics {
    exec { "apt-get-update":
        command => "/usr/bin/apt-get update -qq";
    }
    package {
        [ "build-essential", "git", "subversion", "mercurial", "vim",
          "nfs-common", "openjdk-7-jdk", "tmux", "translate-toolkit",
          "gettext", "htop", "ack-grep", "locate", "sqlite3",
          "python-software-properties", "curl", "axel",
          "libxml2-dev", "libxslt1.1", "libxslt1-dev",
          "libjpeg62", "libjpeg62-dev",
          "libfreetype6", "libfreetype6-dev",
          "libpng12-0", "libpng12-dev",
          "libtidy-0.99-0", "libtidy-dev"]:
            ensure => installed,
            require => Exec['apt-get-update'];
    }
    exec {
        "deadsnakes-ppa":
            command => "/usr/bin/add-apt-repository --yes ppa:fkrull/deadsnakes && apt-get update -qq",
            require => Package["python-software-properties"];
    }
    package {
        [ "python2.6", "python2.6-dev"]:
          ensure => installed,
          require => Exec["deadsnakes-ppa"];
    }
}

# Get apache up and running
class apache {
    package { "libapache2-mod-wsgi":
        ensure => purged;
    }
    package { [ "apache2" ]:
        ensure => present;
    }
}

# Get mysql up and running
class mysql {
    package { [ "mysql-server", "libmysqlclient-dev" ]:
        ensure => present,
    }
}

# Get memcache up and running
class memcache {
    package { [ "memcached", "libmemcached-dev" ]:
        ensure => present,
    }
    service { "memcached":
        ensure => running,
        enable => true,
        require => [ Package["memcached"] ]
    }
}

# Get rabbitmq up and running
class rabbitmq {
    package { ["rabbitmq-server"]:
        ensure => present,
    }
    service { "rabbitmq-server":
        ensure => running,
        enable => true,
        require => [ Package["rabbitmq-server"] ]
    }
}

# Get foreman up and running
class foreman {
    package { "foreman":
        ensure   => 'installed',
        provider => 'gem',
    }
}
