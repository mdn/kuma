# Ansible Role: Node.js

[![Build Status](https://travis-ci.org/geerlingguy/ansible-role-nodejs.svg?branch=master)](https://travis-ci.org/geerlingguy/ansible-role-nodejs)

Installs Node.js on RHEL/CentOS or Debian/Ubuntu.

## Requirements

Requires the EPEL repository on RedHat/CentOS (you can install it by simply adding the `geerlingguy.repo-epel` role to your playbook).

## Role Variables

Available variables are listed below, along with default values (see `defaults/main.yml`):

    nodejs_version: "0.12"

The Node.js version to install. "0.12" is the default and works on all supported OSes. Other versions such as "0.10", "4.x", "5.x", and "6.x" should work on the latest versions of Debian/Ubuntu and RHEL/CentOS.

    nodejs_install_npm_user: "{{ ansible_ssh_user }}"

The user for whom the npm packages will be installed can be set here, this defaults to ansible_user

    npm_config_prefix: "~/.npm-global"

The global installation directory. This should be writeable by the nodejs_install_npm_user.

    npm_config_unsafe_perm: "false"

Set to true to suppress the UID/GID switching when running package scripts. If set explicitly to false, then installing as a non-root user will fail.

    nodejs_npm_global_packages: []

Add a list of npm packages with a `name` and (optional) `version` to be installed globally. For example:

    nodejs_npm_global_packages:
      # Install a specific version of a package.
      - name: jslint
        version: 0.9.3
      # Install the latest stable release of a package.
      - name: node-sass

## Dependencies

None.

## Example Playbook

    - hosts: utility
      vars_files:
        - vars/main.yml
      roles:
        - geerlingguy.nodejs

*Inside `vars/main.yml`*:

    nodejs_npm_global_packages:
      - name: jslint
      - name: node-sass

## License

MIT / BSD

## Author Information

This role was created in 2014 by [Jeff Geerling](http://www.jeffgeerling.com/), author of [Ansible for DevOps](https://www.ansiblefordevops.com/).
