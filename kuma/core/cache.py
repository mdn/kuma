from django.core.cache import get_cache

# just a helper to not have to redefine that all over the place
memcache = get_cache('memcache')
