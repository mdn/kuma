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

By default kuma is configured to print the email it sends in your console
when you run it as plain text. That means the full raw source of every email
will be visible where you run ``foreman start`` or ``./manage.py runserver``
manually.

In case you want to override that default (not recommended) to have the emails
really being sent out, you need to override a setting by modifying your
``.env`` file in the root directory of the kuma source code. Set the
``EMAIL_URL`` variable in ``.env`` like so::

    EMAIL_URL = 'smtp://'

If you have ``sendmail`` installed and working, that should do it. However, you
might get caught in spam filters. An easy workaround for spam filters or not
having sendmail working is to send email via a Gmail account.

Add to your ``.env`` file::

    EMAIL_URL = 'smtps://<your gmail address>:<your gmail password>@smtp.gmail.com:587/'

Yeah, you need to put your Gmail password in a plain text file on your
computer. It's not for everyone. Be **very** careful copying and pasting
settings from ``.env`` if you go this route.

The ``.env`` file should **never** checked into Git and is therefore listed
the ``.gitignore`` file.
