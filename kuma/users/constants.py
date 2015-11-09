import re

from django.utils.translation import ugettext_lazy as _


USERNAME_CHARACTERS = _(u'Username may contain only letters, numbers, and '
                        u'these characters: . - _ +')
USERNAME_REGEX = re.compile(r'^[\w.+-]+$')
USERNAME_LEGACY_REGEX = re.compile(r'^.+$')
