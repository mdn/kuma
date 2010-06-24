import urllib

from django.core import paginator
from django.utils.encoding import smart_str

import wikimarkup

from .models import WikiPage


def paginate(request, queryset, per_page=20):
    """Get a Paginator, abstracting some common paging actions."""
    p = paginator.Paginator(queryset, per_page)

    # Get the page from the request, make sure it's an int.
    try:
        page = int(request.GET.get('page', 1))
    except ValueError:
        page = 1

    # Get a page of results, or the first page if there's a problem.
    try:
        paginated = p.page(page)
    except (paginator.EmptyPage, paginator.InvalidPage):
        paginated = p.page(1)

    base = request.build_absolute_uri(request.path)

    items = [(k, v) for k in request.GET if k != 'page'
             for v in request.GET.getlist(k) if v]

    qsa = urlencode(items)

    paginated.url = u'%s?%s' % (base, qsa)
    return paginated


def urlencode(items):
    """A Unicode-safe URLencoder."""

    try:
        return urllib.urlencode(items)
    except UnicodeEncodeError:
        return urllib.urlencode([(k, smart_str(v)) for k, v in items])


class WikiParser(object):
    """
    Wrapper for wikimarkup. Adds Kitsune-specific callbacks and setup.
    """

    def __init__(self):
        # Register this hook so it gets called
        self.wikimarkup = wikimarkup
        wikimarkup.registerInternalLinkHook(None, self.hookInternalLink)

    def parse(self, text, showToc=True):
        return self.wikimarkup.parse(text, showToc)

    def hookInternalLink(self, parser, space, name):
        """Parses text and returns internal link."""
        link = name
        text = name

        # Split on pipe -- [[href|name]]
        separator = name.find('|')
        if separator != -1:
            link, text = link.split('|', 1)

        # Sections use _, page names use +
        hash_pos = link.find('#')
        hash = ''
        if hash_pos != -1:
            link, hash = link.split('#', 1)

        if hash != '':
            hash = '#' + hash.replace(' ', '_')

        # Links to this page can just contain href="#hash"
        if link == '' and hash != '':
            return u'<a href="%s">%s</a>' % (hash, text)

        try:
            link = WikiPage.objects.get(pageName=link).get_url()
        except WikiPage.DoesNotExist:
            link = WikiPage.get_create_url(link)

        return u'<a href="%s%s">%s</a>' % (link, hash, text)
