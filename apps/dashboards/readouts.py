"""Data aggregators for dashboards"""

from django.conf import settings
from django.utils.timesince import timesince

import jingo
from tower import ugettext as _, ugettext_lazy as _lazy

from wiki.models import Document


def localizable_docs():
    """Return a Queryset of the Documents which are in the default locale,
    approved, and allow translations."""
    return Document.objects.exclude(current_revision=None).filter(
               locale=settings.WIKI_DEFAULT_LANGUAGE, is_localizable=True)


def overview_rows(locale):
    """Return the iterable of dicts needed to draw the Overview table."""
    # The Overview table is a special case: it has only a static number of
    # rows, so it has no expanded, all-rows view, and thus needs no slug, no
    # "max" kwarg on rows(), etc. It doesn't fit the Readout signature, so we
    # don't shoehorn it in.

    total = localizable_docs().count()
    if locale == settings.WIKI_DEFAULT_LANGUAGE:
        translated = total
    else:
        # How many approved documents are there in German that have parents?
        # TODO: Make sure caching doesn't foil this.
        translated = Document.objects.filter(locale=locale).exclude(
            current_revision=None).exclude(parent=None).count()
    return [dict(title=_('All Knowledge Base Articles'),
                 numerator=translated, denominator=total,
                 percent=(int(round(translated / float(total) * 100)) if total
                          else 100),
                 description=_('How many of the approved English '
                               'articles which allow translations '
                               'have an approved translation into this '
                               'language')),
            # TODO: Enable after we integrate WebTrends stats:
#             dict(title=_('Most Viewed Articles'),
#                  numerator=0, denominator=1,
#                  percent=0,
#                  description=_('These are the top 15-20 most visited English'
#                                ' articles, which in sum account for over 50%'
#                                ' of the total traffic to the English '
#                                'Knowledge Base.'))
           ]


class Readout(object):
    """Abstract class representing one table on the Localization Dashboard

    Describing these as atoms gives us the whole-page details views for free.

    """
    #title = _lazy(u'Localized Title of Readout')
    #slug = 'URL slug for detail page and CSS class for table'

    def rows(self, max=None):
        """Return an iterable of dicts containing the data for the table.

        Limit to `max` rows.

        """
        raise NotImplementedError

    def render(self, rows):
        """Return HTML table rows for the given data.

        Default implementation renders a template named after the value of
        self.slug in the dashboards/includes/localization directory.

        """
        return jingo.render_to_string(
            self.request,
            'dashboards/includes/localization/%s.html' % self.slug,
            {'rows': rows})


class UntranslatedReadout(Readout):
    title = _lazy(u'Untranslated Articles')
    slug = 'untranslated'

    def __init__(self, request):
        """`request.locale` must not be the default locale."""
        self.request = request

    def rows(self, max=None):
        # TODO: Optimize so there isn't another query per doc to get the
        # current_revision. Use the method from
        # http://www.caktusgroup.com/blog/2009/09/28/custom-joins-with-djangos-
        # queryjoin/.
        rows = Document.objects.raw('SELECT english.* FROM wiki_document '
            'english RIGHT OUTER JOIN wiki_revision ON '
            'english.current_revision_id=wiki_revision.id LEFT OUTER JOIN '
            'wiki_document translated ON english.id=translated.parent_id AND '
            'translated.locale=%s WHERE translated.id IS NULL AND '
            'english.current_revision_id IS NOT NULL AND '
            'english.is_localizable AND english.locale=%s ORDER BY '
            'wiki_revision.reviewed DESC',
            params=[self.request.locale, settings.WIKI_DEFAULT_LANGUAGE])
        for d in rows[:max] if max else rows:
            # TODO: i18nize better. Show only 1 unit of time: for example,
            # weeks instead of weeks+days or months instead of months+weeks.
            #
            # Not ideal but free:
            ago = (d.current_revision.reviewed and
                   _('%s ago') % timesince(d.current_revision.reviewed))
            yield (dict(title=d.title,
                        url=d.get_absolute_url(),
                        visits=0, percent=0,
                        updated=ago))
