-- Does a quick anonymization of a kuma database. Note that this does
-- not necessarily clear out all confidential information and should
-- not be considered approval to distribute this kuma database.
-- Talk to lcrouch if you have questions.

UPDATE auth_user SET
    email = CONCAT('user',id,'@example.com'),
    password = 'sha256$f538347e82$5098e89186fd307d4bb6fe29ac476e72cf96175617fa933a9bd6b3d89a8b0946'; -- 'testpass'

TRUNCATE notifications_eventwatch;

TRUNCATE django_session;

UPDATE django_site SET
    domain = 'kuma-stage.mozilla.org',
    name = 'kuma-stage.mozilla.org';
