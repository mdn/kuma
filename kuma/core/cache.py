from django.core.cache import caches

# just a helper to not have to redefine that all over the place
redis = caches['redis']
