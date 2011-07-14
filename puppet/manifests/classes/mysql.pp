# Get mysql up and running

class mysql {
    package { "mysql-server": ensure => installed; }
    package { "mysql-devel": ensure => installed; }
}
