from collections import namedtuple
import json
import os

Language = namedtuple(u'Language', u'english native iso639_1')

file = os.path.join(os.path.dirname(__file__), 'languages.json')
locales = json.loads(open(file, 'r').read())

LOCALES = {}

for k in locales:
    LOCALES[k] = Language(locales[k]['english'], locales[k]['native'],
                          locales[k]['iso639_1'])
