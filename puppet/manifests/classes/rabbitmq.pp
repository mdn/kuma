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
