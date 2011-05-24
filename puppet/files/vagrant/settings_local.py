from settings import *

DEBUG = True
DEV = True
TEMPLATE_DEBUG = DEBUG
SERVE_MEDIA = DEBUG

DEMO_UPLOADS_ROOT = '/home/vagrant/uploads/demos'
DEMO_UPLOADS_URL = '/uploads/demos/'

PROD_DETAILS_DIR = '/home/vagrant/product_details_json'
MDC_PAGES_DIR    = '/home/vagrant/mdc_pages'

DEKIWIKI_ENDPOINT = "http://localhost/"

RECAPTCHA_USE_SSL = False
RECAPTCHA_PUBLIC_KEY = '6LdX8cISAAAAAA9HRXmzrcRSFsUoIK9u0nWpvGS_'
RECAPTCHA_PRIVATE_KEY = '6LdX8cISAAAAACkC1kqYmpeSf-1geTmLzrLnq0t6'

BITLY_USERNAME = 'lmorchard'
BITLY_API_KEY = "R_2653e6351e31d02988b3da31dac6e2c0"

# The default database should point to the master.
DATABASES = {
    'default': {
        'NAME': 'kuma',
        'ENGINE': 'django.db.backends.mysql',
        'HOST': 'localhost',
        'USER': 'kuma',
        'PASSWORD': 'kuma',
        'OPTIONS': {'init_command': 'SET storage_engine=InnoDB'},
    },
}

# Use IP:PORT pairs separated by semicolons.
#CACHE_BACKEND = 'django_pylibmc.memcached://localhost:11211?timeout=500'
CACHE_BACKEND = 'locmem://'

# This is used to hash some things in Django.
SECRET_KEY = 'jenny8675309'

LOG_LEVEL = logging.WARNING

DEBUG_PROPAGATE_EXCEPTIONS = DEBUG

