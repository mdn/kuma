# Download, build, and install the Sphinx search server

class sphinx {

    exec {
        "sphinx_download":
            cwd => "$PROJ_DIR/puppet/cache",
            command => "/usr/bin/wget http://sphinxsearch.com/files/sphinx-0.9.9.tar.gz",
            creates => "$PROJ_DIR/puppet/cache/sphinx-0.9.9.tar.gz";
        "sphinx_unpack":
            cwd => "$PROJ_DIR/puppet/cache", 
            command => "/bin/tar xfzv sphinx-0.9.9.tar.gz",
            creates => "$PROJ_DIR/puppet/cache/sphinx-0.9.9",
            require => Exec['sphinx_download'];
        "sphinx_install":
            cwd => "$PROJ_DIR/puppet/cache/sphinx-0.9.9", 
            command => "$PROJ_DIR/puppet/cache/sphinx-0.9.9/configure --enable-id64 && /usr/bin/make && /usr/bin/make install",
            creates => "/usr/local/bin/searchd", 
            require => Exec['sphinx_unpack'];
    }

}
