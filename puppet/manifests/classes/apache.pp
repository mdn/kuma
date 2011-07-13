# Get apache up and running

class apache {
    package { ["mod_ssl", "httpd", "httpd-devel"]: 
        ensure => present,
    }
}
