from __future__ import unicode_literals

import urllib

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import F, OuterRef, Q, Subquery

from kuma.core.urlresolvers import reverse
from kuma.wiki.models import Document, Revision


class Command(BaseCommand):
    """
    See https://bugzilla.mozilla.org/show_bug.cgi?id=1551999 for more
    background.
    This script tries to solve this but it tries to be as generic as possible
    because the problem could re-appear.
    Generally we hope to not have to run this (manually) on a recurring basis.
    """

    help = (
        "Due to a bug, at some point certain edits were made where a new "
        "revision was created but the document's 'current_revision' wasn't "
        "moved with it. This script attempts to rectify that."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--edit',
            action='store_true',
            dest='edit',
            default=False,
            help='Actually edit the current revision of documents found')
        parser.add_argument(
            '--baseurl',
            help='Base URL to site',
            default=settings.SITE_URL)
        parser.add_argument('slugsearch', nargs='*')

    @transaction.atomic()
    def handle(self, *args, **options):
        actually_edit = options['edit']

        def get_url(doc, name='wiki.document', *args):
            return '{}{}'.format(
                options['baseurl'],
                urllib.quote(
                    reverse(name, locale=doc.locale, args=(doc.slug,) + args)))

        documents = Document.objects.all()
        if options['slugsearch']:
            q = Q()
            for slugsearch in options['slugsearch']:
                q |= Q(slug__contains=slugsearch)
            documents = documents.filter(q)
            self.stdout.write("Found slugs: {!r}".format(
                list(documents.values_list('slug', flat=True))
            ))

        newest = Revision.objects.filter(
            document=OuterRef('pk')
        ).order_by('-created')
        documents = documents.annotate(
            newest_revision_id=Subquery(newest.values('pk')[:1])
        )
        for document in documents.exclude(
            current_revision_id=F('newest_revision_id')
        ):
            self.stdout.write('DOCUMENT: {}'.format(get_url(document)))
            self.stdout.write('\tHistory: {}'.format(
                get_url(document, 'wiki.document_revisions')
            ))
            first = True
            revisions = Revision.objects.filter(document=document)
            for revision in revisions.order_by('-created'):
                current = revision.id == document.current_revision_id
                self.stdout.write('\tRevision: {} of {}: {} created {}'.format(
                    revision.id,
                    ('CURRENT' if current else 'NOT CURRENT').ljust(11),
                    get_url(document, 'wiki.revision', revision.id),
                    revision.created
                ))
                if first:
                    if actually_edit:
                        document.make_current()
                    else:
                        self.stderr.write('\tNOT editing at the moment!')
                if current:
                    break
                first = False
            self.stdout.write('\n')
