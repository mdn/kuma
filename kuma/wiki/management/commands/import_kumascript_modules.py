"""
Import KumaScript auto-loaded modules from production site.

Run this when setting up a new dev box to get the latest required KumaScript
modules from the production site.
"""
import requests

from django.core.management.base import BaseCommand

from kuma.users.models import User
from kuma.wiki.exceptions import SlugCollision
from kuma.wiki.models import Document, Revision

KS_AUTOLOAD_MODULES = [
    'Template:mdn:common',
    'Template:DekiScript:Date',
    'Template:DekiScript:Page',
    'Template:DekiScript:String',
    'Template:DekiScript:Uri',
    'Template:DekiScript:Web',
    'Template:DekiScript:Wiki',
]

RAW_TEMPLATE_URL = 'https://developer.mozilla.org/en-US/docs/%s?raw=1'


class Command(BaseCommand):

    def handle(self, *args, **options):
        # get first user to be the creator
        u = User.objects.all()[0]
        loaded_docs = []
        skipped_docs = []

        for slug in KS_AUTOLOAD_MODULES:
            template_response = requests.get(RAW_TEMPLATE_URL % slug)
            doc = Document(title=slug, slug=slug)
            try:
                doc.save()
                loaded_docs.append(slug)
            except SlugCollision:
                # skip modules already in the db
                skipped_docs.append(slug)
                continue
            rev = Revision(document=doc, content=template_response.content,
                           creator=u)
            rev.save()

        print "Loaded docs:"
        for slug in loaded_docs:
            print "%s" % slug
        print "\nSkipped docs that were already loaded:"
        for slug in skipped_docs:
            print "%s" % slug
