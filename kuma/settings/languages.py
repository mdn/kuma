from collections import namedtuple
from os.path import dirname
import json
import os

from decouple import config
from django.utils.translation import ugettext_lazy as _

_Language = namedtuple(u'Language', u'english native translation')

ROOT = dirname(dirname(dirname(os.path.abspath(__file__))))

def path(*parts):
    return os.path.join(ROOT, *parts)

# Directory for product-details files.
PROD_DETAILS_DIR = config('PROD_DETAILS_DIR',
                          default=path('..', 'product_details_json'))

# Accepted locales
MDN_LANGUAGES = (
    'en-US',
    'af',
    'ar',
    'az',
    'bm',
    'bn-BD',
    'bn-IN',
    'ca',
    'cs',
    'de',
    'ee',
    'el',
    'es',
    'fa',
    'ff',
    'fi',
    'fr',
    'fy-NL',
    'ga-IE',
    'ha',
    'he',
    'hi-IN',
    'hr',
    'hu',
    'id',
    'ig',
    'it',
    'ja',
    'ka',
    'ko',
    'ln',
    'mg',
    'ml',
    'ms',
    'my',
    'nl',
    'pl',
    'pt-BR',
    'pt-PT',
    'ro',
    'ru',
    'son',
    'sq',
    'sr',
    'sr-Latn',
    'sv-SE',
    'sw',
    'ta',
    'th',
    'tl',
    'tn',
    'tr',
    'uk',
    'vi',
    'wo',
    'xh',
    'yo',
    'zh-CN',
    'zh-TW',
    'zu',
)

def _get_languages_and_locales():
    """Generates LANGUAGES and LOCALES data

    .. Note::

       This requires product-details data. If product-details data hasn't been
       retrieved, then this prints a warning and then returns empty values. We
       do this because in the case of pristine dev environments, you can't
       update product-details because product-details isn't there, yet.

    """
    languages = []
    locales = {}
    lang_file = os.path.join(PROD_DETAILS_DIR, 'languages.json')
    try:
        json_locales = json.load(open(lang_file, 'r'))
    except IOError as ioe:
        print('Warning: Cannot open %s because it does not exist. LANGUAGES '
              'and LOCALES will be empty. Please run "./manage.py '
              'update_product_details".' % lang_file)
        print(ioe)
        return [], {}

    for locale, meta in json_locales.items():
        locales[locale] = _Language(meta['English'],
                                    meta['native'],
                                    _(meta['English']))
    languages = sorted(tuple([(i, locales[i].native) for i in MDN_LANGUAGES]),
                       key=lambda lang: lang[0])

    return languages, locales


LANGUAGES, LOCALES = _get_languages_and_locales()
