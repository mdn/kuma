# -*- coding: utf-8 -*-
"""
Manually schedule the removal of one or more documents from the document API.
"""
from __future__ import division
from __future__ import unicode_literals

from collections import namedtuple

from django.core.management.base import BaseCommand, CommandError

from kuma.api.tasks import unpublish


class Command(BaseCommand):
    args = '<document_path document_path ...>'
    help = 'Remove one or more documents from the document API'

    def add_arguments(self, parser):
        parser.add_argument(
            'paths',
            help='Path to document(s), like /en-US/docs/Web',
            nargs='*',
            metavar='path')

    def handle(self, *args, **options):
        Logger = namedtuple('Logger', 'info, error')
        log = Logger(info=self.stdout.write, error=self.stderr.write)
        paths = options['paths']
        if not paths:
            raise CommandError('Need at least one document path to remove')
        doc_locale_slug_pairs = []
        for path in paths:
            if path.startswith('/'):
                path = path[1:]
            locale, sep, slug = path.partition('/')
            head, sep, tail = slug.partition('/')
            if head == 'docs':
                slug = tail
            doc_locale_slug_pairs.append((locale, slug))
        unpublish(doc_locale_slug_pairs, log=log)
