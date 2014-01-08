import logging

CELERY_ALWAYS_EAGER = True
ES_LIVE_INDEX = False

logging.getLogger('django.db.backends').setLevel(logging.ERROR)
