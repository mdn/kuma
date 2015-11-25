# Changelog

## 1.4.0

* Bugfixes: item.vhost silently changed to item.name breaking the API
  involuntary.
* Add a simple Travis-CI support
* Update the tasks directory layout to be more idiomatic
* Add a test to ensure the default configuration listen to the good port

## 1.3.0

* Add support for Redhat
* Allow the test to run with TLS by adding dummy certificates
* Allow a more flexible naming for the X.509 certificates

## 1.2.0

* Add the possibility to define the VM to use for testing from the command line
* Switch the default VM used for test to one from Vagrant cloud
* Support the default Debian package instead of the one distributed by RabbitMQ
* Reorganise and clean the code for to help future change (new OS/distrib,
  clustering)

## 1.1.0

* Add the possibility to use non default node name. See the new field `node` in
  the `rabbitmq_vhost_definitions` and `rabbitmq_users_definitions` variables.
  This field is optional.
* Add the possibility to generate a `rabbitmq-env.conf` file in the RabbitMQ
  configuration folder. See the `rabbitmq_conf_env` hash.

## 1.0.0

Initial version number
