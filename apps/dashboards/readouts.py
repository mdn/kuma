# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""Data aggregators for dashboards"""

from django.conf import settings
from django.db import connections, router
from django.utils.datastructures import SortedDict

import jingo
from tower import ugettext as _, ugettext_lazy as _lazy

from dashboards.models import THIS_WEEK, ALL_TIME, PERIODS
from sumo.urlresolvers import reverse
from wiki.models import Document, MEDIUM_SIGNIFICANCE, MAJOR_SIGNIFICANCE


MOST_VIEWED = 1
MOST_RECENT = 2


def _cursor():
    """Return a DB cursor for reading."""
    return connections[router.db_for_read(Document)].cursor()


def overview_rows(locale):
    """Return the iterable of dicts needed to draw the Overview table."""
    def percent_or_100(num, denom):
        return int(round(num / float(denom) * 100)) if denom else 100

    # The Overview table is a special case: it has only a static number of
    # rows, so it has no expanded, all-rows view, and thus needs no slug, no
    # "max" kwarg on rows(), etc. It doesn't fit the Readout signature, so we
    # don't shoehorn it in.
    total = Document.uncached.exclude(current_revision=None).filter(
                locale=settings.WIKI_DEFAULT_LANGUAGE,
                is_localizable=True).count()

    # How many approved documents are there in German that have parents?
    translated = Document.uncached.filter(locale=locale).exclude(
        current_revision=None).exclude(parent=None).count()

    # Of the top 20 most visited English articles, how many are not translated
    # into German?
    TOP_N = 20
    cursor = _cursor()
    cursor.execute(
        'SELECT count(*) FROM '
            '(SELECT trans.id FROM dashboards_wikidocumentvisits '
                'LEFT JOIN wiki_document trans '
                'ON dashboards_wikidocumentvisits.document_id=trans.parent_id '
                'AND trans.locale=%s '
             'WHERE dashboards_wikidocumentvisits.period=%s '
             'ORDER BY dashboards_wikidocumentvisits.visits DESC '
             'LIMIT %s) t1 '
        'WHERE t1.id IS NOT NULL',
        (locale, THIS_WEEK, TOP_N))
    popular_translated = cursor.fetchone()[0]

    return [dict(title=_('Most-Visited Articles'),
                 url='#' + MostVisitedTranslationsReadout.slug,
                 numerator=popular_translated, denominator=TOP_N,
                 percent=percent_or_100(popular_translated, TOP_N),
                 description=_('These are the top 20 most visited articles, '
                               'which account for over 50% of the traffic to '
                               'the Knowledge Base.')),
            dict(title=_('All Knowledge Base Articles'),
                 numerator=translated, denominator=total,
                 percent=percent_or_100(translated, total),
                 description=_('How many of the approved English articles '
                               'which allow translations have an approved '
                               'translation into this language'))]


class Readout(object):
    """Abstract class representing one table on the Localization Dashboard

    Describing these as atoms gives us the whole-page details views for free.

    """
    # title = _lazy(u'Title of Readout')
    # short_title= = _lazy(u'Short Title of Readout for In-Page Links')
    # slug = 'URL slug for detail page'
    # details_link_text = _lazy(u'All articles from this readout...')
    column3_label = _lazy(u'Visits this week')
    column4_label = _lazy(u'Status')
    modes = [(MOST_VIEWED, _lazy('Most Viewed')),
             (MOST_RECENT, _lazy('Most Recent'))]

    def __init__(self, request, locale=None, mode=None):
        """Take request so the template can use contextual macros that need it.

        Renders the data for the locale specified by the request, but you can
        override it by passing another in `locale`.

        """
        self.request = request
        self.locale = locale or request.locale
        self.mode = mode or self.modes[0][1]
        # self.mode is allowed to be invalid.

    def rows(self, max=None):
        """Return an iterable of dicts containing the data for the table.

        This default implementation calls _query_and_params and _format_row.
        You can either implement those or, if you need more flexibility,
        override this.

        Limit to `max` rows.

        """
        cursor = _cursor()
        cursor.execute(*self._query_and_params(max))
        return [self._format_row(r) for r in cursor.fetchall()]

    def render(self, max_rows=None):
        """Return HTML table rows, optionally limiting to a number of rows."""
        # Compute percents for bar widths:
        rows = self.rows(max_rows)
        max_visits = max(r['visits'] for r in rows) if rows else 0
        for r in rows:
            visits = r['visits']
            r['percent'] = (0 if visits is None or not max_visits
                            else int(round(visits / float(max_visits) * 100)))

        # Render:
        return jingo.render_to_string(
            self.request,
            'dashboards/includes/kb_readout.html',
            {'rows': rows, 'column3_label': self.column3_label,
             'column4_label': self.column4_label})

    # To override:

    def _query_and_params(self, max):
        """Return a tuple: (query, params to bind it to)."""
        raise NotImplementedError

    def _format_row(self, row):
        """Turn a DB row tuple into a dict for the template."""
        raise NotImplementedError

    # Convenience methods:

    @staticmethod
    def _limit_clause(max):
        """Return a SQL LIMIT clause limiting returned rows to `max`.

        Return '' if max is None.

        """
        return ' LIMIT %i' % max if max else ''


class MostVisitedDefaultLanguageReadout(Readout):
    title = _lazy(u'Most-Visited Articles')
    # No short_title; the link to this one is hard-coded in Overview readout
    details_link_text = _lazy(u'All knowledge base articles...')
    slug = 'most-visited'
    column3_label = _lazy(u'Visits')
    modes = PERIODS
    review_statuses = {
        1: (_lazy(u'Review Needed'), 'wiki.document_revisions'),
        0: (u'', '')}

    def _query_and_params(self, max):
        # Review Needed: link to /history.
        return ('SELECT engdoc.slug, engdoc.title, '
                'dashboards_wikidocumentvisits.visits, '
                'count(engrev.document_id) '
               'FROM wiki_document engdoc '
               'LEFT JOIN dashboards_wikidocumentvisits ON '
                   'engdoc.id=dashboards_wikidocumentvisits.document_id '
                   'AND dashboards_wikidocumentvisits.period=%s '
               'LEFT JOIN wiki_revision engrev ON '
                   'engrev.document_id=engdoc.id '
                   'AND engrev.reviewed IS NULL '
                   'AND engrev.id>engdoc.current_revision_id '
               'WHERE engdoc.locale=%s '
               'GROUP BY engdoc.id '
               'ORDER BY dashboards_wikidocumentvisits.visits DESC, '
                        'engdoc.title ASC' + self._limit_clause(max),
            (ALL_TIME if self.mode == ALL_TIME else THIS_WEEK, self.locale))

    def _format_row(self, (slug, title, visits, num_unreviewed)):
        needs_review = int(num_unreviewed > 0)
        status, view_name = self.review_statuses[needs_review]
        return (dict(title=title,
                     url=reverse('wiki.document', args=[slug],
                                 locale=self.locale),
                     visits=visits,
                     status=status,
                     status_url=reverse(view_name, args=[slug],
                                        locale=self.locale)
                                if view_name else ''))


class MostVisitedTranslationsReadout(MostVisitedDefaultLanguageReadout):
    slug = 'most-visited-translations'

    # L10n: Replace "English" with your language.
    details_link_text = _lazy(u'All translations in English...')

    significance_statuses = {
        MEDIUM_SIGNIFICANCE: (_lazy(u'Update Needed'), 'wiki.edit_document'),
        MAJOR_SIGNIFICANCE: (_lazy(u'Out of Date'), 'wiki.edit_document')}

    def _query_and_params(self, max):
        # Out of Date or Update Needed: link to /edit.
        # Review Needed: link to /history.
        # These match the behavior of the corresponding readouts.
        return ('SELECT transdoc.slug, transdoc.title, '
                'dashboards_wikidocumentvisits.visits, '
                # The most significant approved change to the English article
                # since the English revision the current translated revision is
                # based on:
                '(SELECT MAX(engrev.significance) '
                 'FROM wiki_revision engrev, wiki_revision transrev '
                 'WHERE engrev.is_approved '
                 'AND transrev.id=transdoc.current_revision_id '
                 'AND engrev.document_id=transdoc.parent_id '
                 'AND engrev.id>transrev.based_on_id '
                '), '
                # Whether there are any unreviewed revs of the translation made
                # since the current one:
                '(SELECT EXISTS '
                    '(SELECT * '
                     'FROM wiki_revision transrev '
                     'WHERE transrev.document_id=transdoc.id '
                     'AND transrev.reviewed IS NULL '
                     'AND transrev.id>transdoc.current_revision_id '
                    ')'
                ') '
               'FROM wiki_document transdoc '
               'LEFT JOIN dashboards_wikidocumentvisits ON transdoc.parent_id='
                   'dashboards_wikidocumentvisits.document_id '
                   'AND dashboards_wikidocumentvisits.period=%s '
               'WHERE transdoc.locale=%s '
               'ORDER BY dashboards_wikidocumentvisits.visits DESC, '
                        'transdoc.title ASC' + self._limit_clause(max),
            (ALL_TIME if self.mode == ALL_TIME else THIS_WEEK, self.locale))

    def _format_row(self, (slug, title, visits, significance, needs_review)):
        status, view_name = self.significance_statuses.get(
                                significance,
                                self.review_statuses[needs_review])
        return (dict(title=title,
                     url=reverse('wiki.document', args=[slug],
                                 locale=self.locale),
                     visits=visits,
                     status=status,
                     status_url=reverse(view_name, args=[slug],
                                        locale=self.locale)
                                if view_name else ''))


class UntranslatedReadout(Readout):
    title = _lazy(u'Untranslated Articles')
    short_title = _lazy(u'Untranslated')
    details_link_text = _lazy(u'All untranslated articles...')
    slug = 'untranslated'
    column4_label = _lazy(u'Updated')

    def _query_and_params(self, max):
        # Incidentally, we tried this both as a left join and as a search
        # against an inner query returning translated docs, and the left join
        # yielded a faster-looking plan (on a production corpus).
        return ('SELECT parent.slug, parent.title, '
            'wiki_revision.reviewed, dashboards_wikidocumentvisits.visits '
            'FROM wiki_document parent '
            'INNER JOIN wiki_revision ON '
                'parent.current_revision_id=wiki_revision.id '
            'LEFT JOIN wiki_document translated ON '
                'parent.id=translated.parent_id AND translated.locale=%s '
            'LEFT JOIN dashboards_wikidocumentvisits ON '
                'parent.id=dashboards_wikidocumentvisits.document_id AND '
                'dashboards_wikidocumentvisits.period=%s '
            'WHERE '
            'translated.id IS NULL AND parent.is_localizable AND '
            'parent.locale=%s '
            + self._order_clause() + self._limit_clause(max),
            (self.locale, THIS_WEEK, settings.WIKI_DEFAULT_LANGUAGE))

    def _order_clause(self):
        return ('ORDER BY wiki_revision.reviewed DESC, parent.title ASC'
                if self.mode == MOST_RECENT
                else 'ORDER BY dashboards_wikidocumentvisits.visits DESC, '
                     'parent.title ASC')

    def _format_row(self, (slug, title, reviewed, visits)):
        # Run the data through the model to (potentially) format it and
        # take advantage of SPOTs (like for get_absolute_url()):
        d = Document(slug=slug, title=title,
                     locale=settings.WIKI_DEFAULT_LANGUAGE)
        return (dict(title=d.title,
                     url=d.get_absolute_url(),
                     visits=visits,
                     updated=reviewed))


class OutOfDateReadout(Readout):
    title = _lazy(u'Out-of-Date Translations')
    short_title = _lazy(u'Out-of-Date')
    details_link_text = _lazy(u'All out-of-date translations...')
    slug = 'out-of-date'
    column4_label = _lazy(u'Out of date since')

    # To show up in this readout, an article's revision since the last
    # approved translation must have a maximum significance equal to this
    # value:
    _max_significance = MAJOR_SIGNIFICANCE

    def _query_and_params(self, max):
        # At the moment, the "Out of Date Since" column shows the time since
        # the translation was out of date at a MEDIUM level of severity or
        # higher. We could arguably knock this up to MAJOR, but technically it
        # is out of date when the original gets anything more than typo
        # corrections.
        return ('SELECT transdoc.slug, transdoc.title, engrev.reviewed, '
            'dashboards_wikidocumentvisits.visits '
            'FROM wiki_document transdoc '
            'INNER JOIN wiki_revision engrev ON engrev.id='
            # The oldest english rev to have an approved level-30 change since
            # the translated doc had an approved rev based on it. NULL if there
            # is none:
                '(SELECT min(id) FROM wiki_revision '
                # Narrow engrev rows to those representing revision of parent
                # doc:
                'WHERE wiki_revision.document_id=transdoc.parent_id '
                # For the purposes of computing the "Out of Date Since" column,
                # the revision that threw the translation out of date had
                # better be more recent than the one the current translation is
                # based on:
                'AND wiki_revision.id>'
                    '(SELECT based_on_id FROM wiki_revision basedonrev '
                    'WHERE basedonrev.id=transdoc.current_revision_id) '
                'AND wiki_revision.significance>=%s '
                'AND %s='
                # Completely filter out outer selections where 30 is not the
                # max signif of english revisions since trans was last
                # approved. Other maxes will be shown by other readouts.
                # Optimize: try "30 IN" if MySQL's statistics gatherer is
                # stupid/nonexistent; the inner query should be able to bail
                # out early. [Ed: No effect on EXPLAIN on admittedly light test
                # corpus.]
                  '(SELECT MAX(engsince.significance) '
                  'FROM wiki_revision engsince '
                  'WHERE engsince.document_id=transdoc.parent_id '
                  # Assumes that any approved revision became the current
                  # revision at some point: we don't let the user go back and
                  # approve revisions older than the latest approved one.
                  'AND engsince.is_approved '
                  'AND engsince.id>'
                  # The English revision the current translation's based on:
                    '(SELECT based_on_id FROM wiki_revision basedonrev '
                    'WHERE basedonrev.id=transdoc.current_revision_id) '
                  ')'
                ') '
            # Join up the visits table for stats:
            'LEFT JOIN dashboards_wikidocumentvisits ON '
                'engrev.document_id=dashboards_wikidocumentvisits.document_id '
                'AND dashboards_wikidocumentvisits.period=%s '
            'WHERE transdoc.locale=%s '
            + self._order_clause() + self._limit_clause(max),
            (MEDIUM_SIGNIFICANCE, self._max_significance, THIS_WEEK,
                self.locale))

    def _order_clause(self):
        return ('ORDER BY engrev.reviewed DESC'
                if self.mode == MOST_RECENT
                else 'ORDER BY dashboards_wikidocumentvisits.visits DESC, '
                     'transdoc.title ASC')

    def _format_row(self, (slug, title, reviewed, visits)):
        return (dict(title=title,
                     url=reverse('wiki.edit_document', args=[slug]),
                     visits=visits, updated=reviewed))


class NeedingUpdatesReadout(OutOfDateReadout):
    title = _lazy(u'Translations Needing Updates')
    short_title = _lazy(u'Needing Updates')
    details_link_text = _lazy(u'All translations needing updates...')
    slug = 'needing-updates'

    _max_significance = MEDIUM_SIGNIFICANCE


class UnreviewedReadout(Readout):
    title = _lazy(u'Unreviewed Changes')
    # ^ Not just changes to translations but also unreviewed chanages to docs
    # in this locale that are not translations

    short_title = _lazy(u'Unreviewed', 'document')
    details_link_text = _lazy(u'All articles requiring review...')
    slug = 'unreviewed'
    column4_label = _lazy(u'Changed')

    def _query_and_params(self, max):
        english_id = ('id' if self.locale == settings.WIKI_DEFAULT_LANGUAGE
                      else 'parent_id')
        return ('SELECT wiki_document.slug, wiki_document.title, '
            'MAX(wiki_revision.created) maxcreated, '
            'GROUP_CONCAT(DISTINCT auth_user.username '
                         "ORDER BY wiki_revision.id SEPARATOR ', '), "
            'dashboards_wikidocumentvisits.visits '
            'FROM wiki_document '
            'INNER JOIN wiki_revision ON '
                        'wiki_document.id=wiki_revision.document_id '
            'INNER JOIN auth_user ON wiki_revision.creator_id=auth_user.id '
            'LEFT JOIN dashboards_wikidocumentvisits ON '
                'wiki_document.' + english_id
                    + '=dashboards_wikidocumentvisits.document_id AND '
                'dashboards_wikidocumentvisits.period=%s '
            'WHERE wiki_revision.reviewed IS NULL '
            'AND (wiki_document.current_revision_id IS NULL OR '
                 'wiki_revision.id>wiki_document.current_revision_id) '
            'AND wiki_document.locale=%s '
            'GROUP BY wiki_document.id '
            + self._order_clause() + self._limit_clause(max),
            (THIS_WEEK, self.locale))

    def _order_clause(self):
        return ('ORDER BY maxcreated DESC'
                if self.mode == MOST_RECENT
                else 'ORDER BY dashboards_wikidocumentvisits.visits DESC, '
                     'wiki_document.title ASC')

    def _format_row(self, (slug, title, changed, users, visits)):
        return (dict(title=title,
                     url=reverse('wiki.document_revisions', args=[slug],
                                 locale=self.locale),
                     visits=visits,
                     updated=changed,
                     users=users))


# L10n Dashboard tables that have their own whole-page views:
L10N_READOUTS = SortedDict((t.slug, t) for t in
    [MostVisitedTranslationsReadout, UntranslatedReadout, OutOfDateReadout,
     NeedingUpdatesReadout, UnreviewedReadout])

# Contributors ones:
CONTRIBUTOR_READOUTS = SortedDict((t.slug, t) for t in
    [MostVisitedDefaultLanguageReadout, UnreviewedReadout])

# All:
READOUTS = L10N_READOUTS.copy()
READOUTS.update(CONTRIBUTOR_READOUTS)
