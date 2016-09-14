# -*- coding: utf-8 -*-
# This file was generated with the command:
#   ./manage.py generate_languages_settings
# The source files are:
#   kuma/settings/mdn_languages.txt
#   kuma/settings/languages.json
# See the documentation for more information:
#   https://kuma.readthedocs.io/en/latest/localization.html

from __future__ import unicode_literals
from collections import namedtuple

from django.utils.translation import ugettext_lazy as _

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
    'zu'
)

# Mozilla's language data for MDN_LANGUAGES
_Language = namedtuple(u'Language', u'english native translation')
LOCALES = {
    'en-US': _Language(
        'English (US)',
        'English (US)',
        _('English (US)')),
    'af': _Language(
        'Afrikaans',
        'Afrikaans',
        _('Afrikaans')),
    'ar': _Language(
        'Arabic',
        'عربي',
        _('Arabic')),
    'az': _Language(
        'Azerbaijani',
        'Azərbaycanca',
        _('Azerbaijani')),
    'bm': _Language(
        'Bambara',
        'Bamanankan',
        _('Bambara')),
    'bn-BD': _Language(
        'Bengali (Bangladesh)',
        'বাংলা (বাংলাদেশ)',
        _('Bengali (Bangladesh)')),
    'bn-IN': _Language(
        'Bengali (India)',
        'বাংলা (ভারত)',
        _('Bengali (India)')),
    'ca': _Language(
        'Catalan',
        'Català',
        _('Catalan')),
    'cs': _Language(
        'Czech',
        'Čeština',
        _('Czech')),
    'de': _Language(
        'German',
        'Deutsch',
        _('German')),
    'ee': _Language(
        'Ewe',
        'Eʋe',
        _('Ewe')),
    'el': _Language(
        'Greek',
        'Ελληνικά',
        _('Greek')),
    'es': _Language(
        'Spanish',
        'Español',
        _('Spanish')),
    'fa': _Language(
        'Persian',
        'فارسی',
        _('Persian')),
    'ff': _Language(
        'Fulah',
        'Pulaar-Fulfulde',
        _('Fulah')),
    'fi': _Language(
        'Finnish',
        'suomi',
        _('Finnish')),
    'fr': _Language(
        'French',
        'Français',
        _('French')),
    'fy-NL': _Language(
        'Frisian',
        'Frysk',
        _('Frisian')),
    'ga-IE': _Language(
        'Irish',
        'Gaeilge',
        _('Irish')),
    'ha': _Language(
        'Hausa',
        'Hausa',
        _('Hausa')),
    'he': _Language(
        'Hebrew',
        'עברית',
        _('Hebrew')),
    'hi-IN': _Language(
        'Hindi (India)',
        'हिन्दी (भारत)',
        _('Hindi (India)')),
    'hr': _Language(
        'Croatian',
        'Hrvatski',
        _('Croatian')),
    'hu': _Language(
        'Hungarian',
        'magyar',
        _('Hungarian')),
    'id': _Language(
        'Indonesian',
        'Bahasa Indonesia',
        _('Indonesian')),
    'ig': _Language(
        'Igbo',
        'Igbo',
        _('Igbo')),
    'it': _Language(
        'Italian',
        'Italiano',
        _('Italian')),
    'ja': _Language(
        'Japanese',
        '日本語',
        _('Japanese')),
    'ka': _Language(
        'Georgian',
        'ქართული',
        _('Georgian')),
    'ko': _Language(
        'Korean',
        '한국어',
        _('Korean')),
    'ln': _Language(
        'Lingala',
        'Lingála',
        _('Lingala')),
    'mg': _Language(
        'Malagasy',
        'Malagasy',
        _('Malagasy')),
    'ml': _Language(
        'Malayalam',
        'മലയാളം',
        _('Malayalam')),
    'ms': _Language(
        'Malay',
        'Melayu',
        _('Malay')),
    'my': _Language(
        'Burmese',
        'မြန်မာဘာသာ',
        _('Burmese')),
    'nl': _Language(
        'Dutch',
        'Nederlands',
        _('Dutch')),
    'pl': _Language(
        'Polish',
        'Polski',
        _('Polish')),
    'pt-BR': _Language(
        'Portuguese (Brazilian)',
        'Português (do Brasil)',
        _('Portuguese (Brazilian)')),
    'pt-PT': _Language(
        'Portuguese (Portugal)',
        'Português (Europeu)',
        _('Portuguese (Portugal)')),
    'ro': _Language(
        'Romanian',
        'Română',
        _('Romanian')),
    'ru': _Language(
        'Russian',
        'Русский',
        _('Russian')),
    'son': _Language(
        'Songhai',
        'Soŋay',
        _('Songhai')),
    'sq': _Language(
        'Albanian',
        'Shqip',
        _('Albanian')),
    'sr': _Language(
        'Serbian',
        'Српски',
        _('Serbian')),
    'sr-Latn': _Language(
        'Serbian',
        'Srpski',
        _('Serbian')),
    'sv-SE': _Language(
        'Swedish',
        'Svenska',
        _('Swedish')),
    'sw': _Language(
        'Swahili',
        'Kiswahili',
        _('Swahili')),
    'ta': _Language(
        'Tamil',
        'தமிழ்',
        _('Tamil')),
    'th': _Language(
        'Thai',
        'ไทย',
        _('Thai')),
    'tl': _Language(
        'Tagalog',
        'Tagalog',
        _('Tagalog')),
    'tn': _Language(
        'Tswana',
        'Setswana',
        _('Tswana')),
    'tr': _Language(
        'Turkish',
        'Türkçe',
        _('Turkish')),
    'uk': _Language(
        'Ukrainian',
        'Українська',
        _('Ukrainian')),
    'vi': _Language(
        'Vietnamese',
        'Tiếng Việt',
        _('Vietnamese')),
    'wo': _Language(
        'Wolof',
        'Wolof',
        _('Wolof')),
    'xh': _Language(
        'Xhosa',
        'isiXhosa',
        _('Xhosa')),
    'yo': _Language(
        'Yoruba',
        'Yorùbá',
        _('Yoruba')),
    'zh-CN': _Language(
        'Chinese (Simplified)',
        '中文 (简体)',
        _('Chinese (Simplified)')),
    'zh-TW': _Language(
        'Chinese (Traditional)',
        '正體中文 (繁體)',
        _('Chinese (Traditional)')),
    'zu': _Language(
        'Zulu',
        'isiZulu',
        _('Zulu'))
}
