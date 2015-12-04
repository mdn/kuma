from settings_test import *

ES_LIVE_INDEX = True
ES_DISABLED = False
ES_DEFAULT_NUM_REPLICAS = 0
# See the following URL on why we set num_shards to 1 for tests:
# http://www.elasticsearch.org/guide/en/elasticsearch/guide/current/relevance-is-broken.html
ES_DEFAULT_NUM_SHARDS = 1
