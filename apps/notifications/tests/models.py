# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from django.db import models

from notifications.models import NotificationsMixin


# TODO: figure out why placing the mixin *after* models.Model fails
# See also http://code.djangoproject.com/ticket/10249
class MockModel(NotificationsMixin, models.Model):
    pass
