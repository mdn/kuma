# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

# Install python and compiled modules for project
class python_prereqs {
    package {
        [ "python2.7", "python2.7-dev", "python-setuptools",
            "python-virtualenv", "python-pip", "python-imaging",
            "python-mysqldb", "python-pylibmc", "python-jinja2",
            "python-coverage", "ipython", "python-sqlparse",
            "python-pyquery", "python-pygments", "pylint", "pyflakes",
            "libapache2-mod-wsgi",
            "libxml2-dev", "libxslt1.1", "libxslt1-dev", "libjpeg62",
            "libjpeg62-dev", "libfreetype6", "libfreetype6-dev", "libpng12-0",
            "libpng12-dev", "libtidy-0.99-0", "libtidy-dev" ]:
            ensure => installed;
    }
    file { "/vagrant/puppet/cache/pip":
        ensure => directory
    }
}

class python_modules {
    exec { 
         "pip-install-compiled":
             cwd => '/tmp', 
             timeout => 1200, # Too long, but this can take awhile
             command => "/usr/bin/pip install --download-cache=/vagrant/puppet/cache/pip -r /vagrant/requirements/compiled.txt";
         "pip-install-dev":
             cwd => '/tmp', 
             timeout => 1200, # Too long, but this can take awhile
             command => "/usr/bin/pip install --download-cache=/vagrant/puppet/cache/pip -r /vagrant/requirements/dev.txt";
     }
}

class python {
    include python_prereqs, python_modules
    Class['python_prereqs'] -> Class['python_modules']
}
