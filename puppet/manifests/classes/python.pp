# Install python and compiled modules for project
class python_prereqs {
    # cleaning up for old sake's
    package {
        [ "python-setuptools", "python-virtualenv", "python-pip",
          "python-imaging", "python-mysqldb", "python-pylibmc",
          "python-jinja2", "python-coverage", "ipython", "python-sqlparse",
          "python-pyquery", "python-pygments", "pyflakes"]:
          ensure => purged;
    }
    exec {
        "get-pip":
            cwd => '/tmp',
            command => '/usr/bin/curl -LO https://bootstrap.pypa.io/get-pip.py',
            creates => '/tmp/get-pip.py',
            require => Package["curl"];
        # will install setuptools, too
        "install-pip":
            cwd => '/tmp',
            require => [Exec["get-pip"], Package["python2.7"]],
            command => '/usr/bin/python2.7 get-pip.py && /bin/rm get-pip.py',
            creates => '/usr/local/bin/pip2.7';
        "install-extras":
            require => Exec["install-pip"],
            command => '/usr/local/bin/pip2.7 install virtualenv';
        "create-virtualenv":
            cwd => '/home/vagrant',
            require => Exec["install-extras"],
            command => '/bin/rm -rf env && /usr/bin/sudo -H -u vagrant /usr/local/bin/virtualenv env',
            user => 'vagrant';
    }
}


class python_reqs {
    exec {
        "install-reqs":
            cwd => '/home/vagrant/src',
            timeout => 1200, # Too long, but this can take awhile
            command => "/usr/bin/sudo -H -u vagrant /home/vagrant/env/bin/pip install -r requirements/compiled.txt -r requirements/docs.txt";
     }
}

class python {
    include python_prereqs, python_reqs
    Class['python_prereqs'] -> Class['python_reqs']
}
