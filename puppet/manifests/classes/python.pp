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
        require => Package['python26-distribute']
    }
}

class python_modules {
    exec { 
        "pip-install-modules":
            cwd => '/tmp', 
            timeout => 3600, # Too long, but this can take awhile
            command => "/usr/bin/pip install -r $PROJ_DIR/requirements/dev.txt -r $PROJ_DIR/requirements/compiled.txt";
    }
}

class python {
    include python_prereqs, python_modules
    Class['python_prereqs'] -> Class['python_modules']
}
