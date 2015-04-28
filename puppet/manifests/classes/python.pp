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
            command => '/usr/bin/curl -LO https://raw.github.com/pypa/pip/master/contrib/get-pip.py',
            creates => '/tmp/get-pip.py',
            require => Package["axel"];
        # will install setuptools, too
        "install-pip":
            cwd => '/tmp',
            require => [Exec["get-pip"], Package["python2.6"]],
            command => '/usr/bin/python2.6 get-pip.py && /bin/rm get-pip.py',
            creates => '/usr/local/bin/pip2.6';
    }
    exec {
        "install-extras":
            require => Exec["install-pip"],
            command => '/usr/local/bin/pip2.6 install virtualenv';
    }
    exec {
        "create-virtualenv":
            cwd => '/home/vagrant',
            require => Exec["install-extras"],
            command => '/bin/rm -rf env && /usr/local/bin/virtualenv -p /usr/bin/python2.6 env',
            user => 'vagrant';
    }
}


class python_reqs {
    exec {
        "install-reqs":
            cwd => '/home/vagrant/src',
            timeout => 1200, # Too long, but this can take awhile
            command => "/home/vagrant/env/bin/pip install -r requirements/dev.txt -r requirements/compiled.txt -r requirements/docs.txt",
            user => 'vagrant';
     }
}

class python {
    include python_prereqs, python_reqs
    Class['python_prereqs'] -> Class['python_reqs']
}
