import datetime

from django.conf import settings
from django.core.management.base import NoArgsCommand
from django.shortcuts import render
from django.test import RequestFactory, override_settings
from django.utils import translation

from html5lib import constants as html5lib_constants

from kuma.wiki.content import parse


class Command(NoArgsCommand):

    def handle(self, *args, **options):

        # Not ideal, but we need to temporarily remove inline elements as a
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
        request.LANGUAGE_CODE = settings.LANGUAGE_CODE  # for Jinja2
        translation.activate(settings.LANGUAGE_CODE)  # for context var LANG
        host = 'developer.mozilla.org'
        request.META['SERVER_NAME'] = host
        this_year = datetime.date.today().year
        # Load the page with sphinx template
        with override_settings(
                ALLOWED_HOSTS=[host],
                SITE_URL=settings.PRODUCTION_URL,
                DEBUG=False):
            response = render(request, 'wiki/sphinx.html',
                              {'is_sphinx': True,
                               'this_year': this_year})
        content = response.content

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

        # Make in-comment script src absolute for IE
        content = content.replace('src="/static/',
                                  'src="%s/static/' % settings.PRODUCTION_URL)

        # Fix missing DOCTYPE
        assert content.startswith("<html")
        content = u"<!DOCTYPE html>\n" + content

        # Output the response
        print content.encode('utf8')
