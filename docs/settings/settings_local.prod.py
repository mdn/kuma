from settings import *

DEBUG = False
TEMPLATE_DEBUG = False

# The default database should point to the master.
DATABASES = {
    'default': {
        'NAME': 'kitsune',
        'ENGINE': 'django.db.backends.mysql',
        'HOST': '',
        'USER': '',
        'PASSWORD': '',
        'OPTIONS': {'init_command': 'SET storage_engine=InnoDB'},
    },
}

# This is used to hash some things in Django.
SECRET_KEY = 'replace me with something long and random'

DEBUG_PROPAGATE_EXCEPTIONS = DEBUG
