# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

# Get node.js and npm installed under CentOS 
class nodejs {
    package {
        [ "nodejs", "nodejs-dev", "npm" ]:
            ensure => installed;
    }
    file { "/usr/include/node":
        target => "/usr/include/nodejs",
        ensure => link,
        require => Package['nodejs-dev']
    }
    exec { 'npm-install':
        cwd => "/vagrant/kumascript",
        user => "vagrant",
        command => "/usr/bin/npm install",
        creates => "/vagrant/kumascript/node_modules/fibers",
        require => [
            Package["nodejs"], Package["nodejs-dev"], Package["npm"],
            File["/usr/include/node"],
        ]
    }
}
