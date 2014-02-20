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
    file { "/home/vagrant/src/puppet/cache/pip":
        ensure => directory
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
        "install-wheel":
            require => Exec["install-pip"],
            command => '/usr/local/bin/pip2.6 install wheel';
    }
}


class python_wheels {
    exec {
        "download-wheels":
            cwd => "/home/vagrant/src/puppet/cache/wheels",
            command => "/usr/bin/axel -a https://s3-us-west-2.amazonaws.com/pkgs.mozilla.net/python/mdn/wheels.tar.xz && /bin/tar xvfJ *.tar.xz && /bin/rm wheels.tar.xz",
            creates => '/home/vagrant/src/puppet/cache/wheels/wheels';
        "install-wheels":
            cwd => '/home/vagrant/src',
            timeout => 1200, # Too long, but this can take awhile
            command => "/usr/local/bin/pip2.6 install --no-index --find-links=/home/vagrant/src/puppet/cache/wheels/wheels -r requirements/prod.txt -r requirements/dev.txt -r requirements/compiled.txt",
            require => Exec["download-wheels"];
        "clean-wheels":
            cwd => "/home/vagrant/src/puppet/cache/wheels",
            command => "/bin/rm -rf wheels",
            require => Exec["install-wheels"];
     }
}

class python {
    include python_prereqs, python_wheels
    Class['python_prereqs'] -> Class['python_wheels']
}
