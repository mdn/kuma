from os import listdir, makedirs
from os.path import isdir, join, exists
from io import open
from sys import stderr
from subprocess import Popen, PIPE
from shutil import rmtree
import json

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import connection
from django.utils.translation import activate

from kuma.core.templatetags.jinja_helpers import url

locale_dir = 'locale'
dest_dir = join('jinja2', 'includes', 'prebuilt-react-components')

class Command(BaseCommand):
    help = 'Pre-build React.js components.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clean',
            help='Cleaning previous build result',
            action='store_true',
            default=False)

    def handle(self, *arg, **kwargs):
        if kwargs['clean'] and exists(dest_dir):
            rmtree(dest_dir)

        locales = [
            x for x in listdir(locale_dir)
            if x != 'templates' and isdir(join(locale_dir, x))
        ]

        components_contexts = {}

        for locale_code in locales:
            activate(locale_code)
            components_contexts[locale_code] = {
                'Logo': {'props': {'url': url('home')}},
            }

        json_input = json.dumps(components_contexts, indent=2)
        cmd = ['npm', 'run', '--silent', 'react-prebuild']
        p = Popen(cmd, stdin=PIPE, stdout=PIPE, stderr=stderr)
        p.stdin.write(json_input)
        p.stdin.close()
        parsed = json.loads(p.stdout.read())

        if not exists(dest_dir): makedirs(dest_dir)
        for locale_code, components in parsed.iteritems():
            locale_dir_path = join(dest_dir, locale_code)
            if not exists(locale_dir_path): makedirs(locale_dir_path)
            for component_name, html in components.iteritems():
                file_path = join(locale_dir_path, component_name + '.html')
                f = open(file_path, mode='w', encoding='utf-8')
                f.write(html)
                f.close()
