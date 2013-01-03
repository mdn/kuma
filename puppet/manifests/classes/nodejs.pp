# Get node.js and npm installed under CentOS 

class node_repos {
    exec {
        "node_repo_download":
            cwd => "$PROJ_DIR/puppet/cache",
            command => "/usr/bin/wget http://people.mozilla.com/~lorchard/nodejs-stable-release.noarch.rpm",
            creates => "$PROJ_DIR/puppet/cache/nodejs-stable-release.noarch.rpm";
        "node_repo_install":
            cwd => "$PROJ_DIR/puppet/cache",
            command => "/usr/bin/yum localinstall -y --nogpgcheck $PROJ_DIR/puppet/cache/nodejs-stable-release.noarch.rpm",
            creates => "/etc/yum.repos.d/nodejs-stable.repo",
            require => Exec['node_repo_download'];
    }
}

class node_install {
    package {
        [ "nodejs", "nodejs-devel", "npm" ]:
            ensure => installed;
    }
    file { "/usr/bin/node": 
        target => "/usr/bin/nodejs",
        ensure => link, 
        require => Package['nodejs']
    }
    file { "/usr/include/node": 
        target => "/usr/include/nodejs",
        ensure => link, 
        require => Package['nodejs-devel']
    }
}

class nodejs {
    include node_repos, node_install
    Class['node_repos'] -> Class['node_install']
}
