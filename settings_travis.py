from settings_test import *

ES_LIVE_INDEX = True
ES_DISABLED = False

DATABASES = {
    'default': {
        'NAME': 'kuma',
        'ENGINE': 'django.db.backends.mysql',
        'HOST': 'localhost',
        'USER': 'root',
        'PASSWORD': '',
        'OPTIONS': {'init_command': 'SET storage_engine=InnoDB'},
    },
}
