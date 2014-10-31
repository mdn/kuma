===
CGI
===

If all other deployment methods do not work, CGI will work for sure.  CGI
is supported by all major browsers but usually has a less-than-optimal
performance.

This is also the way you can use a Werkzeug application on Google's
`AppEngine`_, there however the execution does happen in a CGI-like
environment.  The application's performance is unaffected because of that.

.. _AppEngine: http://code.google.com/appengine/

Creating a `.cgi` file
======================

First you need to create the CGI application file.  Let's call it
`yourapplication.cgi`::

    #!/usr/bin/python
    from wsgiref.handlers import CGIHandler
    from yourapplication import make_app

    application = make_app()
    CGIHandler().run(application)

If you're running Python 2.4 you will need the :mod:`wsgiref` package.  Python
2.5 and higher ship this as part of the standard library.

Server Setup
============

Usually there are two ways to configure the server.  Either just copy the
`.cgi` into a `cgi-bin` (and use `mod_rerwite` or something similar to
rewrite the URL) or let the server point to the file directly.

In Apache for example you can put a like like this into the config:

.. sourcecode:: apache

    ScriptName /app /path/to/the/application.cgi

For more information consult the documentation of your webserver.
