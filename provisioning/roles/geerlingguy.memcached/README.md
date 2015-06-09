# Ansible Role: Memcached

[![Build Status](https://travis-ci.org/geerlingguy/ansible-role-memcached.svg?branch=master)](https://travis-ci.org/geerlingguy/ansible-role-memcached)

An Ansible Role that installs Memcached on RedHat/CentOS or Debian/Ubuntu Linux.

## Requirements

None.

## Role Variables

Available variables are listed below, along with default values (see `defaults/main.yml`):

    memcached_user: memcache

The user under which the Memcached daemon will run.

    memcached_port: 11211
    memcached_listen_ip: 127.0.0.1

The port and IP address (127.0.0.1 for localhost) on which Memcached will listen for requests.

    memcached_memory_limit: 64
    memcached_connections: 1024

Memcached limits. The maximum amount of RAM `memcached` will consume (64MB is the default), and the maximum number of simultaneous connections memcached will handle.

    memcached_log_file: /var/log/memcached.log

The location of the memcached log file.

## Dependencies

None.

## Example Playbook

    - hosts: cache
      roles:
        - { role: geerlingguy.memcached }

## License

MIT / BSD

## Author Information

This role was created in 2014 by [Jeff Geerling](http://jeffgeerling.com/), author of [Ansible for DevOps](http://ansiblefordevops.com/).
