# -*- coding: utf-8 -*-
"""
Re-render documents without overwhelming the queues.
"""
from django.core.management.base import BaseCommand, CommandError

from kuma.wiki.models import Document
from kuma.wiki.utils import rerender_slow


class Command(BaseCommand):
    help = 'Re-render wiki documents'

    def add_arguments(self, parser):
        parser.add_argument('--all',
                            action='store_true',
                            help='Re-render all documents')
        parser.add_argument('--macro',
                            help='Filter on documents using this macro')
        parser.add_argument('--locale',
                            help='Filter on documents in this locale')

    def handle(self, *args, **options):
        filtered = False
        docs = Document.objects.all()
        instance_filter = None
        macro_name = None
        locale = None

        if options['locale']:
            filtered = True
            locale = options['locale']
            docs = docs.filter(locale=locale)

        if options['macro']:
            filtered = True
            macro_name = options['macro']
            docs = docs.filter(html__icontains=macro_name.lower())

            def macro_filter(doc):
                macros = [x.lower() for x in doc.extract.macro_names()]
                return macro_name.lower() in macros

            instance_filter = macro_filter

        if not filtered and not options['all']:
            raise CommandError('Specify a filter or --all')

        if options['verbosity'] >= 1:
            stream = self.stdout
        else:
            stream = None

        rendered, unrendered, errored, seconds = rerender_slow(
            docs, stream=stream, doc_filter=instance_filter)

        self.stdout.write(('Rendered %d docs, %d left unrendered, %d errored,'
                           ' in %d seconds.')
                          % (rendered, unrendered, len(errored), seconds))
        if errored:
            self.stderr.write('Rendering errors on these documents:')
            for count, doc_id in enumerate(errored):
                doc = Document.objects.get(id=doc_id)
                self.stderr.write('%d: %s' % (count, doc.get_full_url()))
