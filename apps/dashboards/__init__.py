from django.conf import settings

ORDERS = (
    ('last-update', 'Last update'),
)

LOCALIZATION_FLAGS = (
    ('inprogress', 'Localization in Progress'),
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
