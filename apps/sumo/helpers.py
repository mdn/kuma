import cgi
import urllib
import urlparse

from django.conf import settings
from django.core.urlresolvers import reverse

import jinja2

from jingo import register, env
from didyoumean import DidYouMean


@register.filter
def paginator(pager):
    return Paginator(pager).render()


@register.filter
def urlparams(url_, hash=None, **query):
    """
    Add a fragment and/or query paramaters to a URL.

    New query params will be appended to exising parameters, except duplicate
    names, which will be replaced.
    """
    url = urlparse.urlparse(url_)
    fragment = hash if hash is not None else url.fragment

    query_dict = dict(cgi.parse_qsl(url.query)) if url.query else {}
    query_dict.update((k, v) for k, v in query.items() if v is not None)

    query_string = urllib.urlencode(query_dict.items())
    new = urlparse.ParseResult(url.scheme, url.netloc, url.path, url.params,
                               query_string, fragment)
    return jinja2.Markup(new.geturl())


class Paginator(object):

    def __init__(self, pager):
        self.pager = pager

        self.max = 10
        self.span = (self.max - 1) / 2

        self.page = pager.number
        self.num_pages = pager.paginator.num_pages
        self.count = pager.paginator.count

        pager.page_range = self.range()
        pager.dotted_upper = self.count not in pager.page_range
        pager.dotted_lower = 1 not in pager.page_range

    def range(self):
        """Return a list of page numbers to show in the paginator."""
        page, total, span = self.page, self.num_pages, self.span
        if total < self.max:
            lower, upper = 0, total
        elif page < span + 1:
            lower, upper = 0, span * 2
        elif page > total - span:
            lower, upper = total - span * 2, total
        else:
            lower, upper = page - span, page + span - 1
        return range(max(lower + 1, 1), min(total, upper) + 1)

    def render(self):
        c = {'pager': self.pager, 'num_pages': self.num_pages,
             'count': self.count}
        t = env.get_template('layout/paginator.html').render(**c)
        return jinja2.Markup(t)


@register.function
def spellcheck(string, locale='en-US'):
    d = DidYouMean(locale, dict_dir=settings.DICT_DIR)
    return not d.check(string)


@register.filter
@jinja2.contextfilter
def suggestions(context, string, locale='en-US'):
    d = DidYouMean(locale, dict_dir=settings.DICT_DIR)
    words = [(jinja2.escape(w.new), w.corrected) for w in d.suggest(string)]

    newwords = []
    newquery = []
    for w in words:
        newquery.append(w[0])
        if w[1]:
            newwords.append(u'<strong>%s</strong>' % w[0])
        else:
            newwords.append(w[0])

    markup = '<a href="{url}">{text}</a>'

    q = u' '.join(newquery)
    text = u' '.join(newwords)
    query_dict = context['request'].GET.copy()
    query_dict['q'] = q
    if 'page' in query_dict:
        query_dict['page'] = 1

    query_string = urllib.urlencode(query_dict.items())

    url = u'%s?%s' % (reverse('search'), query_string)

    return jinja2.Markup(markup.format(url=jinja2.escape(url), text=text))
