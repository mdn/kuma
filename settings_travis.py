from settings import *

CELERY_ALWAYS_EAGER = False
BROKER_URL = 'amqp://guest:guest@localhost:5672//'

ES_URLS = ['http://localhost:9200']
ES_INDEX_PREFIX = 'mdn'
ES_INDEXES = {'default': 'main_index'}
ES_INDEXING_TIMEOUT = 30
ES_DISABLED = False
