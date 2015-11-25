# Ansible Role: Apache 2.x

[![Build Status](https://travis-ci.org/geerlingguy/ansible-role-apache.svg?branch=master)](https://travis-ci.org/geerlingguy/ansible-role-apache)

An Ansible Role that installs Apache 2.x on RHEL/CentOS and Debian/Ubuntu.

## Requirements

If you are using SSL/TLS, you will need to provide your own certificate and key files. You can generate a self-signed certificate with a command like `openssl req -x509 -nodes -days 365 -newkey rsa:2048 -keyout example.key -out example.crt`.

## Role Variables

Available variables are listed below, along with default values (see `defaults/main.yml`):

    apache_enablerepo: ""

The repository to use when installing Apache (only used on RHEL/CentOS systems). If you'd like later versions of Apache than are available in the OS's core repositories, use a repository like EPEL (which can be installed with the `geerlingguy.repo-epel` role).

    apache_listen_port: 80
    apache_listen_port_ssl: 443

The ports on which apache should be listening. Useful if you have another service (like a reverse proxy) listening on port 80 or 443 and need to change the defaults.

    apache_create_vhosts: true
    apache_vhosts_filename: "vhosts.conf"

If set to true, a vhosts file, managed by this role's variables (see below), will be created and placed in the Apache configuration folder. If set to false, you can place your own vhosts file into Apache's configuration folder and skip the convenient (but more basic) one added by this role.

    apache_vhosts:
      # Additional optional properties: 'serveradmin, serveralias, extra_parameters'.
      - {servername: "local.dev", documentroot: "/var/www/html"}

Add a set of properties per virtualhost, including `servername` (required), `documentroot` (required), `serveradmin` (optional), `serveralias` (optional) and `extra_parameters` (optional: you can add whatever additional configuration lines you'd like in here).

    apache_vhosts_ssl: []

No SSL vhosts are configured by default, but you can add them using the same pattern as `apache_vhosts`, with a few additional directives, like the following example:

    apache_vhosts_ssl:
      - {
        servername: "local.dev",
        documentroot: "/var/www/html",
        certificate_file: "/home/vagrant/example.crt",
        certificate_key_file: "/home/vagrant/example.key",
        certificate_chain_file: "/path/to/certificate_chain.crt"
      }

Other SSL directives can be managed with other SSL-related role variables.

    apache_ssl_protocol: "All -SSLv2 -SSLv3"
    apache_ssl_cipher_suite: "AES256+EECDH:AES256+EDH"

The SSL protocols and cipher suites that are used/allowed when clients make secure connections to your server. These are secure/sane defaults, but for maximum security, performand, and/or compatibility, you may need to adjust these settings.

    apache_mods_enabled:
      - rewrite.load
      - ssl.load

(Debian/Ubuntu ONLY) Which Apache mods to enable (these will be symlinked into the apporopriate location). See the `mods-available` directory inside the apache configuration directory (`/etc/apache2/mods-available` by default) for all the available mods.

## Dependencies

None.

## Example Playbook

    - hosts: webservers
      vars_files:
        - vars/main.yml
      roles:
        - { role: geerlingguy.apache }

*Inside `vars/main.yml`*:

    apache_listen_port: 8080
    apache_vhosts:
      - {servername: "example.com", documentroot: "/var/www/vhosts/example_com"}

## License

MIT / BSD

## Author Information

This role was created in 2014 by [Jeff Geerling](http://jeffgeerling.com/), author of [Ansible for DevOps](http://ansiblefordevops.com/).
