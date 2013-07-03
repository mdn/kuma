# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import logging

from django.conf import settings


# fill this in for django 1.4
class RequireDebugTrue(logging.Filter):
    def filter(self, record):
        return settings.DEBUG
