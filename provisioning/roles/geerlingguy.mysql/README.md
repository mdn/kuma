# Ansible Role: MySQL

[![Build Status](https://travis-ci.org/geerlingguy/ansible-role-mysql.svg?branch=master)](https://travis-ci.org/geerlingguy/ansible-role-mysql)

Installs MySQL server on RHEL/CentOS or Debian/Ubuntu servers.

## Requirements

None.

## Role Variables

Available variables are listed below, along with default values (see `vars/main.yml`):

    mysql_user_home: /root

The home directory inside which Python MySQL settings will be stored, which Ansible will use when connecting to MySQL. This should be the home directory of the user which runs this Ansible role.

    mysql_root_password: root

The MySQL root user account password.

    mysql_enabled_on_startup: yes

Whether MySQL should be enabled on startup.

    overwrite_global_mycnf: yes

Whether the global my.cnf should be overwritten each time this role is run. Setting this to `no` tells Ansible to only create the `my.cnf` file if it doesn't exist. This should be left at its default value (`yes`) if you'd like to use this role's variables to configure MySQL.

    mysql_databases: []

The MySQL databases to create. A database has the values `name`, `encoding` (defaults to `utf8`), `collation` (defaults to `utf8_general_ci`) and `replicate` (defaults to `1`, only used if replication is configured). The formats of these are the same as in the `mysql_db` module.

    mysql_users: []

The MySQL users and their privileges. A user has the values `name`, `host` (defaults to `localhost`), `password` and `priv` (defaults to `*.*:USAGE`). The formats of these are the same as in the `mysql_user` module.

    mysql_packages:
      - mysql
      - mysql-server
      - MySQL-python

(OS-specific, RedHat/CentOS defaults listed here) Packages to be installed. In some situations, you may need to add additional packages, like `mysql-devel`.

    mysql_enablerepo: ""

(RedHat/CentOS only) If you have enabled any additional repositories (might I suggest geerlingguy.repo-epel or geerlingguy.repo-remi), those repositories can be listed under this variable (e.g. `remi,epel`). This can be handy, as an example, if you want to install later versions of MySQL.

    mysql_port: "3306"
    mysql_bind_address: '0.0.0.0'
    mysql_datadir: /var/lib/mysql

Default MySQL connection configuration.

    mysql_log: ""
    mysql_log_error: /var/log/mysqld.log
    mysql_syslog_tag: mysqld

MySQL logging configuration. Setting `mysql_log` (the general query log) or `mysql_log_error` to `syslog` will make MySQL log to syslog using the `mysql_syslog_tag`.

    mysql_slow_query_log_enabled: no
    mysql_slow_query_log_file: /var/log/mysql-slow.log
    mysql_slow_query_time: 2

Slow query log settings. Note that the log file will be created by this role, but if you're running on a server with SELinux or AppArmor, you may need to add this path to the allowed paths for MySQL, or disable the mysql profile. For example, on Debian/Ubuntu, you can run `sudo ln -s /etc/apparmor.d/usr.sbin.mysqld /etc/apparmor.d/disable/usr.sbin.mysqld && sudo service apparmor restart`.

    mysql_key_buffer_size: "256M"
    mysql_max_allowed_packet: "64M"
    mysql_table_open_cache: "256"
    [...]

The rest of the settings in `defaults/main.yml` control MySQL's memory usage. The default values are tuned for a server where MySQL can consume ~512 MB RAM, so you should consider adjusting them to suit your particular server better.

    mysql_server_id: "1"
    mysql_max_binlog_size: "100M"
    mysql_expire_logs_days: "10"
    mysql_replication_role: ''
    mysql_replication_master: ''
    mysql_replication_user: []

Replication settings. Set `mysql_server_id` and `mysql_replication_role` by server (e.g. the master would be ID `1`, with the `mysql_replication_role` of `master`, and the slave would be ID `2`, with the `mysql_replication_role` of `slave`). The `mysql_replication_user` uses the same keys as `mysql_users`, and is created on master servers, and used to replicate on all the slaves.

## Dependencies

None.

## Example Playbook

    - hosts: db-servers
      vars_files:
        - vars/main.yml
      roles:
        - { role: geerlingguy.mysql }

*Inside `vars/main.yml`*:

    mysql_root_password: super-secure-password
    mysql_databases:
      - name: example_db
        encoding: latin1
        collation: latin1_general_ci
    mysql_users:
      - name: example_user
        host: "%"
        password: similarly-secure-password
        priv: "example_db.*:ALL"

## License

MIT / BSD

## Author Information

This role was created in 2014 by [Jeff Geerling](http://jeffgeerling.com/), author of [Ansible for DevOps](http://ansiblefordevops.com/).
