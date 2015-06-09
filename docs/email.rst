===============
Email from Kuma
===============

The default settings for Kuma *do not send email*. If you want to get email,
you should double check one thing first: are there any rows in the
``tidings_watch`` table? If there are, you may be sending email to
**real users**. The script in ``scripts/anonymize.sql`` will truncate this
table. Simply run it against your Kuma database::

    mysql -ukuma -pkuma kuma < scripts/anonymize.sql

Sending Email
=============

So now you know you aren't emailing real users, but you'd still like to email
yourself and test email in general. There are a few settings you'll need to
use.

First, set the ``EMAIL_BACKEND``. This document assumes you're using the SMTP
mail backend.

::

    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

If you have ``sendmail`` installed and working, that should do it. However, you
might get caught in spam filters. An easy workaround for spam filters or not
having sendmail working is to send email via a Gmail account.

::

    EMAIL_USE_TLS = True
    EMAIL_PORT = 587
    EMAIL_HOST = 'smtp.gmail.com'
    EMAIL_HOST_USER = '<your gmail address>@gmail.com'
    EMAIL_HOST_PASSWORD = '<your gmail password>'

Yeah, you need to put your Gmail password in a plain text file on your
computer. It's not for everyone. Be **very** careful copying and pasting
settings from ``settings_local.py`` if you go this route.
