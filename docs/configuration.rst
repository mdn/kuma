Configuration
=============

The MDN team uses `Constance <https://pypi.python.org/pypi/django-constance>` to
manage keys that are needed by some services. These keys can be entered into the
Constance configuration page (/admin/constance/config) once the server is up and
running.

This document lists some services that use Constance and the possible values
that can be provided to them.

Facebook Research Application
-----------------------------

MDN has conducted research on which social media services are most popular among
users.

For this research to be conducted on a server, the server needs to be associated
with its own Facebook application. As a result, one Facebook application has
been created for each server the team uses.

The App ID of each application is listed below with its respective server. These
can be entered as values of FACEBOOK_RESEARCH_APP_ID in Constance.

Local
~~~~~

285215675010807

Development
~~~~~~~~~~~

1481224932161730

Staging
~~~~~~~

510387192398202

Production
~~~~~~~~~~

610383632407865
