from django.conf import settings

ORDERS = (
    ('last-update', 'Last update'),
)

TOPICS = ('All', 'HTML', 'CSS', 'JavaScript',)
LOCALES = settings.LANGUAGE_CHOICES
LANGUAGES = settings.MDN_LANGUAGES
DEFAULT_LOCALE = 'en-US'

WAFFLE_FLAG = 'l10ndashboard'
