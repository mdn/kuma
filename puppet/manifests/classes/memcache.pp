# Get memcache up and running

class memcache {
    package { [ "memcached", "memcached-devel" ]:
        ensure => present,
    }
    service { "memcached":
        ensure => running,
        enable => true,
        require => [ Package["memcached"] ]
    }
}
