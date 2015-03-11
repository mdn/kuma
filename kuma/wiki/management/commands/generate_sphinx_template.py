from html5lib import constants as html5lib_constants

from django.conf import settings
from django.core.management.base import NoArgsCommand
from django.shortcuts import render
from django.test import RequestFactory

from tower import ugettext as _

from kuma.wiki.content import parse


class Command(NoArgsCommand):

    def handle(self, *args, **options):

        # Not ideal, but we need to temporarily remove inline elemnents as a
        # void/ignored element
        # TO DO:  Can this clone code be shortened?
        new_void_set = set()
        for item in html5lib_constants.voidElements:
            new_void_set.add(item)
        new_void_set.remove('link')
        new_void_set.remove('img')
        html5lib_constants.voidElements = frozenset(new_void_set)

        # Create a mock request for the sake of rendering the template
        request = RequestFactory().get('/')
        request.locale = settings.LANGUAGE_CODE
        request.META['SERVER_NAME'] = 'developer.mozilla.org'

        # Load the page with sphinx template
        content = render(request, 'wiki/sphinx.html', {'is_sphinx': True,
                                                       'gettext': _}).content

        # Use a filter to make links absolute
        tool = parse(content, is_full_document=True)
        content = tool.absolutizeAddresses(
            base_url=settings.PRODUCTION_URL,
            tag_attributes={
                'a': 'href',
                'img': 'src',
                'form': 'action',
                'link': 'href',
                'script': 'src'
            }).serialize()

        # Output the response
        print content.encode('utf8')
