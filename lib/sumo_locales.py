from collections import namedtuple
import json
import os

Language = namedtuple(u'Language',
                      u'external internal english native dictionary')

file = os.path.join(os.path.dirname(__file__), 'languages.json')
locales = json.loads(open(file, 'r').read())

LOCALES = {}

for k in locales:
    LOCALES[k] = Language(locales[k]['external'], locales[k]['internal'],
                          locales[k]['English'], locales[k]['native'],
                          locales[k]['dictionary'])

INTERNAL_MAP = dict([(LOCALES[k].internal, k) for k in LOCALES])
