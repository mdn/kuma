from django.conf import settings
from product_details import product_details

# a static mapping of lower case language names and their native names
LANGUAGES_DICT = dict([(lang.lower(), product_details.languages[lang]['native'])
                       for lang in settings.MDN_LANGUAGES])
