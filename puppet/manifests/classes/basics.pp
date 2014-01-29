# Get apache up and running
class apache {
    package { [ "apache2" ]:
        ensure => present,
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
