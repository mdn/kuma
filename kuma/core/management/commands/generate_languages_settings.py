# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json
import os.path

from django.conf import settings
from django.core.management.base import BaseCommand

template = """\
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
    '{MDN_LANGUAGES}'
)

# Mozilla's language data for MDN_LANGUAGES
_Language = namedtuple(u'Language', u'english native translation')
LOCALES = {{
    {LOCALES}
}}
"""

locale_template = """\
'{lang}': _Language(
        '{English}',
        '{native}',
        _('{English}'))"""


class Command(BaseCommand):
    help = "Generate kuma/settings/languages.py"

    def handle(self, *args, **options):
        # Get path to settings folder
        settings_path = os.path.join(settings.ROOT, 'kuma', 'settings')

        # Read languages from mdn_languages.txt
        mdn_path = os.path.join(settings_path, 'mdn_languages.txt')
        mdn_languages = []
        with open(mdn_path, 'r') as mdn_file:
            for raw_line in mdn_file:
                line = raw_line.strip()
                if line and line[0] != '#':
                    mdn_languages.append(line)

        # Read English and native names from languages.json
        json_path = os.path.join(settings_path, 'languages.json')
        locale_data = {}
        with open(json_path, 'r') as json_file:
            data = json.load(json_file)
            for lang in mdn_languages:
                locale_data[lang] = data[lang]

        # Format locale entries
        locale_output = []
        for lang in mdn_languages:
            data = locale_data[lang]
            entry = locale_template.format(lang=lang,
                                           English=data['English'],
                                           native=data['native'])
            locale_output.append(entry)

        # Write languages.py
        output = template.format(MDN_LANGUAGES="',\n    '".join(mdn_languages),
                                 LOCALES=',\n    '.join(locale_output))
        output_path = os.path.join(settings_path, 'languages.py')
        with open(output_path, 'wb') as output_file:
            output_file.write(output.encode('utf8'))
