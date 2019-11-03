"""
Manually schedule the cleaning of one or more documents
"""
from math import ceil

from celery import chain
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand, CommandError

from kuma.core.utils import chunked
from kuma.users.models import User
from kuma.wiki.models import Document
from kuma.wiki.tasks import (clean_document_chunk, email_document_progress)


class Command(BaseCommand):
    args = '<document_path document_path ...>'
    help = 'Clean the current revision of one or more wiki documents'

    def add_arguments(self, parser):
        parser.add_argument(
            'paths',
            help='Path to document(s), like /en-US/docs/Web',
            nargs='*',  # overridden by --all or --locale
            metavar='path')
        parser.add_argument(
            '--all',
            help='Clean ALL documents (rather than by path)',
            action='store_true')
        parser.add_argument(
            '--locale',
            help='Clean ALL documents in this locale (rather than by path)')

    def handle(self, *args, **options):
        user = get_or_create_known_user('mdnwebdocs-bot')
        if options['all'] or options['locale']:
            filters = {}
            if options['locale'] and not options['all']:
                locale = options['locale'].decode('utf8')
                self.stdout.write(
                    'Cleaning all documents in locale {}'.format(locale))
                filters.update(locale=locale)
            else:
                self.stdout.write('Cleaning all documents')
            docs = Document.objects.filter(**filters)
            docs = docs.order_by('-modified')
            docs = docs.values_list('id', flat=True)
            self.stdout.write('...found {} documents.'.format(len(docs)))
            chain_clean_docs(docs, user.pk)
        else:
            # Accept page paths from command line, but be liberal
            # in what we accept, eg: /en-US/docs/CSS (full path);
            # /en-US/CSS (no /docs); or even en-US/CSS (no leading slash)
            paths = options['paths']
            if not paths:
                raise CommandError('Need at least one document path to clean')
            for path in paths:
                if path.startswith('/'):
                    path = path[1:]
                locale, sep, slug = path.partition('/')
                head, sep, tail = slug.partition('/')
                if head == 'docs':
                    slug = tail
                try:
                    doc = Document.objects.get(locale=locale, slug=slug)
                    self.stdout.write('Cleaning {!r}'.format(doc))
                    rev = doc.clean_current_revision(user)
                except Exception as e:
                    self.stderr.write('...error: {}'.format(str(e)))
                else:
                    if rev is None:
                        self.stdout.write("...skipped (it's already clean)")
                    else:
                        self.stdout.write('...created {!r}'.format(rev))


def get_or_create_known_user(username):
    user = User.objects.get_or_create(username=username)[0]
    known_authors = Group.objects.get_or_create(name="Known Authors")[0]
    user.groups.add(known_authors)
    return user


def chain_clean_docs(doc_pks, user_pk):
    tasks = []
    count = 0
    total = len(doc_pks)
    n = int(ceil(total / 5))
    chunks = chunked(doc_pks, n)

    for chunk in chunks:
        count += len(chunk)
        tasks.append(clean_document_chunk.si(chunk, user_pk))
        percent_complete = int(ceil((count / total) * 100))
        tasks.append(
            email_document_progress.si('clean_document', percent_complete,
                                       total))

    chain(*tasks).apply_async()
