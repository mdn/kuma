# Install python and compiled modules for project
class python_prereqs {
    package {
        [ "python26-devel", "python26-libs", "python26-distribute",
            "python26-mod_wsgi", "libxml2", "libxml2-devel", "libxslt",
            "libxslt-devel", "libjpeg", "libjpeg-devel", 
            "libmemcached", "libmemcached-devel",
            "libpng", "libpng-devel" ]:
            ensure => installed;
    }
    exec { "pip-install": 
        command => "/usr/bin/easy_install-2.6 -U pip", 
        creates => "/usr/bin/pip",
        timeout => 600,
        require => Package['python26-distribute']
    }
    file { "/vagrant/puppet/cache/pip":
        ensure => directory
    }
    exec { "virtualenv-install": 
        command => "/usr/bin/pip install --download-cache=/vagrant/puppet/cache/pip -U virtualenv", 
        creates => "/usr/bin/virtualenv",
        timeout => 600,
        require => [ Exec['pip-install'], File["/vagrant/puppet/cache/pip"] ]
    }
}

class python_virtualenv {
    exec {
        "virtualenv-create":
            cwd => "/home/vagrant",
            user => "vagrant",
            command => "/usr/bin/virtualenv --no-site-packages /home/vagrant/kuma-venv",
            creates => "/home/vagrant/kuma-venv"
    }
    # This bash_profile auto-activates the virtualenv on login.
    file {
        "/home/vagrant/.bash_profile":
            source => "$PROJ_DIR/puppet/files/home/vagrant/bash_profile",
            owner => "vagrant", group => "vagrant", mode => 0664,
            require => Exec['virtualenv-create'];
    }
}

class python_modules {
    exec { 
         "pip-cache-ownership":
             command => "/bin/chown -R vagrant:vagrant /vagrant/puppet/cache/pip && /bin/chmod ug+rw -R /vagrant/puppet/cache/pip",
             unless => '/bin/su vagrant -c "/usr/bin/test -w /vagrant/puppet/cache/pip"';
         "pip-install-compiled":
             require => Exec['pip-cache-ownership'],
             user => "vagrant",
             cwd => '/tmp', 
             timeout => 600, # Too long, but this can take awhile
             command => "/home/vagrant/kuma-venv/bin/pip install --download-cache=/vagrant/puppet/cache/pip -r $PROJ_DIR/requirements/compiled.txt";
         "pip-install-dev":
             require => Exec['pip-cache-ownership'],
             user => "vagrant",
             cwd => '/tmp', 
             timeout => 600, # Too long, but this can take awhile
             command => "/home/vagrant/kuma-venv/bin/pip install --download-cache=/vagrant/puppet/cache/pip -r $PROJ_DIR/requirements/dev.txt";
     }
}

class python {
    include python_prereqs, python_virtualenv, python_modules
    Class['python_prereqs'] -> Class['python_virtualenv'] -> Class['python_modules']
}
