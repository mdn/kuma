from django.conf import settings

ORDERS = (
    ('-modified', 'Recent locale document'),
    ('modified', 'Oldest locale document'),
    ('-parent__modified', 'Recent En document'),
    ('parent__modified', 'Oldest En document'),
)

LOCALIZATION_FLAGS = (
    ('update-needed', 'Update needed'),
    ('missing-parent', 'Missing parent'),
    ('inprogress', 'Localization in progress'),
)

# TODO: fix this
_langugage_choices = settings.LANGUAGE_CHOICES[:]
try:
    _langugage_choices.remove(('en-US', u'English'))
except ValueError:
    pass
LOCALES = _langugage_choices

LANGUAGES = settings.MDN_LANGUAGES

DEFAULT_LOCALE = 'en-US'

# Flags

WAFFLE_FLAG = 'l10ndashboard'

# Revisions

PAGE_SIZE = 100
