import re
from tower import ugettext_lazy as _

USERNAME_CHARACTERS = _(u'Username may contain only letters, numbers, and '
                        u'these characters: . - _ +')
USERNAME_REGEX = re.compile(r'^[\w.+-]+$')
