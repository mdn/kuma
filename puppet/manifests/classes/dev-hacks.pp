# Do some dirty, dirty things to make development nicer.
class dev_hacks {
    exec { 'locale-gen':
        command => "/usr/sbin/locale-gen en_US.utf8",
        unless => '/bin/grep -q "en_US.utf8" /etc/default/locale'
    }

    exec { 'update-locale':
        command => "/usr/sbin/update-locale LC_ALL='en_US.utf8'",
        unless => '/bin/grep -q "en_US.utf8" /etc/default/locale',
        require => Exec['locale-gen']
    }

    file { "/home/vagrant":
        owner => "vagrant", group => "vagrant", mode => 0755;
    }

    file {
        [ "/home/vagrant/logs",
            "/home/vagrant/uploads",
            "/home/vagrant/product_details_json",
            "/home/vagrant/mdc_pages" ]:
        ensure => directory,
        owner => "vagrant", group => "vagrant", mode => 0777;
    }

    file { "/home/vagrant/src/kumascript_settings_local.json":
        ensure => file,
        source => "/home/vagrant/src/puppet/files/vagrant/kumascript_settings_local.json";
    }

    file { "/etc/motd":
        source => "/home/vagrant/src/puppet/files/etc/motd",
        owner => "root", group => "root", mode => 0644;
    }

    file { "/etc/hosts":
        source => "/home/vagrant/src/puppet/files/etc/hosts",
        owner => "root", group => "root", mode => 0644;
    }

    file { "/etc/hostname":
        source => "/home/vagrant/src/puppet/files/etc/hostname",
        owner => "root", group => "root", mode => 0644;
    }

    file { "/etc/resolv.conf":
        source => "/home/vagrant/src/puppet/files/etc/resolv.conf",
        owner => "root", group => "root", mode => 0644;
    }

}

# Last few things that need doing...
class dev_hacks_post {

    # This bash_profile auto-activates the virtualenv on login, adds some
    # useful things to the $PATH, etc.
    file {
        "/home/vagrant/.bash_profile":
            source => "/home/vagrant/src/puppet/files/home/vagrant/bash_profile",
            owner => "vagrant", group => "vagrant", mode => 0664;
        "/home/vagrant/bin":
            ensure => directory,
            owner => "vagrant", group => "vagrant", mode => 0755;
    }
}
