from .testing import *  # noqa

ES_LIVE_INDEX = False
ES_DEFAULT_NUM_REPLICAS = 0
# See the following URL on why we set num_shards to 1 for tests:
# http://www.elasticsearch.org/guide/en/elasticsearch/guide/current/relevance-is-broken.html
ES_DEFAULT_NUM_SHARDS = 1
