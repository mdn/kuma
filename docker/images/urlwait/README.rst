urlwait
-------

The urlwait image runs a script that repeatedly attempts to connect to a
service URL specified via, by default, the ``DATABASE_URL`` environment
variable, until it is either successful or until it reaches the timeout
specified via the ``URLWAIT_TIMEOUT`` environment variable or the default
timeout of 15 seconds.

See https://github.com/pmclanahan/urlwait.
