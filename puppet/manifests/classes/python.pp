# Install python and compiled modules for project
class python_prereqs {
    # cleaning up for old sake's
    package {
        [ "python-setuptools", "python-virtualenv", "python-pip",
          "python-imaging", "python-mysqldb", "python-pylibmc",
          "python-jinja2", "python-coverage", "ipython", "python-sqlparse",
          "python-pyquery", "python-pygments", "pylint", "pyflakes"]:
          ensure => purged;
    }
    file {
        "/home/vagrant/src/puppet/cache/wheels":
        ensure => directory;
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
            # we install 1.4.9 here separately because 1.4.x can't be packaged as a wheel file
            command => '/usr/local/bin/pip2.6 install wheel virtualenv "Django<1.5"';
    }
    exec {
        "create-virtualenv":
            cwd => '/home/vagrant',
            require => Exec["install-extras"],
            command => '/bin/rm -rf env && /usr/local/bin/virtualenv -p /usr/bin/python2.6 env',
            user => 'vagrant';
    }
}


class python_wheels {
    exec {
        "download-wheels":
            cwd => "/home/vagrant/src/puppet/cache/wheels",
            timeout => 1800, # Too long, but this can take awhile
            command => "/usr/bin/axel https://s3-us-west-2.amazonaws.com/pkgs.mozilla.net/python/mdn/base_wheels.tar.gz && /bin/tar xfz *.tar.gz && /bin/rm base_wheels.tar.gz",
            creates => '/home/vagrant/src/puppet/cache/wheels/base_wheels',
            require => File["/home/vagrant/src/puppet/cache/wheels"],
            user => 'vagrant';
        "install-wheels":
            cwd => '/home/vagrant/src',
            timeout => 1200, # Too long, but this can take awhile
            command => "/home/vagrant/env/bin/pip install --no-index --find-links=/home/vagrant/src/puppet/cache/wheels/base_wheels -r requirements/prod.txt -r requirements/dev.txt -r requirements/compiled.txt",
            require => Exec["download-wheels"],
            user => 'vagrant';
        "clean-wheels":
            cwd => "/home/vagrant/src/puppet/cache/wheels",
            command => "/bin/rm -rf base_wheels",
            require => Exec["install-wheels"],
            user => 'vagrant';
     }
}

class python {
    include python_prereqs, python_wheels
    Class['python_prereqs'] -> Class['python_wheels']
}
