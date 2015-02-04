from settings import *

CELERY_ALWAYS_EAGER = True
ASYNC_SIGNALS = False
ES_URLS = ['localhost:9200']
ES_INDEX_PREFIX = 'mdn'
ES_INDEXES = {'default': 'main_index'}
ES_INDEXING_TIMEOUT = 30
ES_LIVE_INDEX = True
ES_DISABLED = False
