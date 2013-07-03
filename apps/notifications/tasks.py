# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from celery.task import task

from notifications.models import Watch


@task(rate_limit='1/m')
def claim_watches(user):
    """Look for anonymous watches with this user's email and attach them to the
    user."""
    Watch.objects.filter(email=user.email).update(email=None, user=user)
