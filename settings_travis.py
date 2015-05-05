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
        'OPTIONS': {
            'sql_mode': 'TRADITIONAL',
            'charset': 'utf8',
            'init_command': 'SET '
                'storage_engine=INNODB,'
                'character_set_connection=utf8,'
                'collation_connection=utf8_general_ci',
        },
        'ATOMIC_REQUESTS': True,
        'TEST_CHARSET': 'utf8',
        'TEST_COLLATION': 'utf8_general_ci',
    },
}
