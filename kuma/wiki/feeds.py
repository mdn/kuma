"""Feeds for documents"""
import datetime
import json
import urllib

from django.conf import settings
from django.db.models import F
from django.contrib.syndication.views import Feed
from django.utils.html import escape
from django.utils.feedgenerator import (SyndicationFeed, Rss201rev2Feed,
                                        Atom1Feed)
from django.utils.translation import ugettext as _

from kuma.core.urlresolvers import reverse
from kuma.core.validators import valid_jsonp_callback_value
from kuma.users.helpers import gravatar_url

from .helpers import diff_table, tag_diff_table, compare_url, colorize_diff
from .models import Document, Revision


MAX_FEED_ITEMS = getattr(settings, 'MAX_FEED_ITEMS', 500)
DEFAULT_FEED_ITEMS = 50


class DocumentsFeed(Feed):
    title = _('MDN documents')
    subtitle = _('Documents authored by MDN users')
    link = _('/')

    def __call__(self, request, *args, **kwargs):
        self.request = request
        if 'all_locales' in request.GET:
            self.locale = None
        else:
            self.locale = request.locale
        return super(DocumentsFeed, self).__call__(request, *args, **kwargs)

    def feed_extra_kwargs(self, obj):
        return {'request': self.request}

    def item_extra_kwargs(self, obj):
        return {'obj': obj}

    def get_object(self, request, format):
        if format == 'json':
            self.feed_type = DocumentJSONFeedGenerator
        elif format == 'rss':
            self.feed_type = Rss201rev2Feed
        else:
            self.feed_type = Atom1Feed

    def item_pubdate(self, document):
        return document.current_revision.created

    def item_title(self, document):
        return document.title

    def item_description(self, document):
        return document.current_revision.summary

    def item_author_name(self, document):
        return document.current_revision.creator.username

    def item_author_link(self, document):
        return self.request.build_absolute_uri(
            document.current_revision.creator.get_absolute_url())

    def item_link(self, document):
        return self.request.build_absolute_uri(document.get_absolute_url())

    def item_categories(self, document):
        return document.tags.all()


class DocumentJSONFeedGenerator(SyndicationFeed):
    """JSON feed generator for Documents
    TODO: Someday maybe make this into a JSON Activity Stream?"""
    mime_type = 'application/json'

    def _encode_complex(self, obj):
        if isinstance(obj, datetime.datetime):
            return obj.isoformat()

    def write(self, outfile, encoding):
        request = self.feed['request']

        # Check for a callback param, validate it before use
        callback = request.GET.get('callback', None)
        if callback is not None:
            if not valid_jsonp_callback_value(callback):
                callback = None

        items_out = []
        for item in self.items:
            document = item['obj']

            # Include some of the simple elements from the preprocessed item
            item_out = dict((x, item[x]) for x in (
                'link', 'title', 'pubdate', 'author_name', 'author_link',
            ))

            # HACK: DocumentFeed is the superclass of RevisionFeed. In this
            # case, current_revision is the revision itself.
            # TODO: Refactor this out into separate DocumentFeed and
            # RevisionFeed subclasses of Feed.
            if hasattr(document, 'current_revision'):
                revision = document.current_revision
            else:
                revision = document

            item_out['author_avatar'] = gravatar_url(revision.creator)

            summary = revision.summary
            if summary:
                item_out['summary'] = summary

            # Linkify the tags used in the feed item
            categories = dict(
                (x, request.build_absolute_uri(
                    reverse('kuma.wiki.views.list_documents',
                            kwargs={'tag': x})))
                for x in item['categories']
            )
            if categories:
                item_out['categories'] = categories

            items_out.append(item_out)

        data = items_out

        if callback:
            outfile.write('%s(' % callback)
        outfile.write(json.dumps(data, default=self._encode_complex))
        if callback:
            outfile.write(')')


class DocumentsRecentFeed(DocumentsFeed):
    """
    Feed of recently revised documents
    """
    title = _('MDN recent document changes')
    subtitle = _('Recent changes to MDN documents')

    def get_object(self, request, format, tag=None, category=None):
        super(DocumentsRecentFeed, self).get_object(request, format)
        self.category = category
        self.tag = tag
        if tag:
            self.title = _('MDN recent changes to documents tagged %s' % tag)
            self.link = self.request.build_absolute_uri(
                reverse('wiki.tag', args=(tag,)))
        else:
            self.link = self.request.build_absolute_uri(
                reverse('kuma.wiki.views.list_documents'))

    def items(self):
        # Temporarily storing the selected documents PKs in a list
        # to speed up retrieval (max MAX_FEED_ITEMS size)
        item_pks = (Document.objects
                            .filter_for_list(tag_name=self.tag,
                                             category=self.category,
                                             locale=self.locale)
                            .filter(current_revision__isnull=False)
                            .order_by('-current_revision__created')
                            .values_list('pk', flat=True)[:MAX_FEED_ITEMS])
        return (Document.objects.filter(pk__in=list(item_pks))
                                .defer('html')
                                .prefetch_related('current_revision',
                                                  'current_revision__creator',
                                                  'tags'))


class DocumentsReviewFeed(DocumentsRecentFeed):
    """
    Feed of documents in need of review
    """
    title = _('MDN documents in need of review')
    subtitle = _('Recent changes to MDN documents that need to be reviewed')

    def get_object(self, request, format, tag=None):
        super(DocumentsReviewFeed, self).get_object(request, format)
        self.subtitle = None
        if tag:
            self.title = _('MDN documents for %s review' % tag)
            self.link = self.request.build_absolute_uri(
                reverse('kuma.wiki.views.list_documents_for_review',
                        args=(tag,)))
        else:
            self.title = _('MDN documents for review')
            self.link = self.request.build_absolute_uri(
                reverse('kuma.wiki.views.list_documents_for_review'))
        return tag

    def items(self, tag=None):
        # Temporarily storing the selected documents PKs in a list
        # to speed up retrieval (max MAX_FEED_ITEMS size)
        item_pks = (Document.objects
                            .filter_for_review(tag_name=tag, locale=self.locale)
                            .filter(current_revision__isnull=False)
                            .order_by('-current_revision__created')
                            .values_list('pk', flat=True)[:MAX_FEED_ITEMS])
        return (Document.objects.filter(pk__in=list(item_pks))
                                .defer('html')
                                .prefetch_related('current_revision',
                                                  'current_revision__creator',
                                                  'tags'))


class DocumentsUpdatedTranslationParentFeed(DocumentsFeed):
    """Feed of translated documents whose parent has been modified since the
    translation was last updated."""

    def get_object(self, request, format, tag=None):
        super(DocumentsUpdatedTranslationParentFeed,
              self).get_object(request, format)
        self.subtitle = None
        self.title = _("MDN '%s' translations in need of update" %
                       self.locale)
        # TODO: Need an HTML / dashboard version of this feed
        self.link = self.request.build_absolute_uri(
            reverse('kuma.wiki.views.list_documents'))

    def items(self):
        return (Document.objects
                        .prefetch_related('parent')
                        .filter(locale=self.locale, parent__isnull=False)
                        .filter(modified__lt=F('parent__modified'))
                        .order_by('-parent__current_revision__created')
                [:MAX_FEED_ITEMS])

    def item_description(self, item):
        # TODO: Needs to be a jinja template?
        template = _(u"""
            <p>
              <a href="%(parent_url)s" title="%(parent_title)s">
                 View '%(parent_locale)s' parent
              </a>
              (<a href="%(mod_url)s">last modified at %(parent_modified)s</a>)
            </p>
            <p>
              <a href="%(doc_edit_url)s" title="%(doc_title)s">
                  Edit '%(doc_locale)s' translation
              </a>
              (last modified at %(doc_modified)s)
            </p>
        """)
        doc, parent = item, item.parent

        trans_based_on_pk = (Revision.objects.filter(document=parent)
                                             .filter(created__lte=doc.modified)
                                             .order_by('created')
                                             .values_list('pk', flat=True)
                                             .first())
        mod_url = compare_url(parent,
                              trans_based_on_pk,
                              parent.current_revision.id)

        context = {
            'doc_url': self.request.build_absolute_uri(doc.get_absolute_url()),
            'doc_edit_url': self.request.build_absolute_uri(
                reverse('wiki.edit_document', args=[doc.slug])),
            'doc_title': doc.title,
            'doc_locale': doc.locale,
            'doc_modified': doc.modified,
            'parent_url': self.request.build_absolute_uri(
                parent.get_absolute_url()),
            'parent_title': parent.title,
            'parent_locale': parent.locale,
            'parent_modified': parent.modified,
            'mod_url': mod_url,
        }
        return template % context


class RevisionsFeed(DocumentsFeed):
    """
    Feed of recent revisions
    """
    title = _('MDN recent revisions')
    subtitle = _('Recent revisions to MDN documents')

    def items(self):
        items = Revision.objects
        limit = int(self.request.GET.get('limit', DEFAULT_FEED_ITEMS))
        page = int(self.request.GET.get('page', 1))

        start = (page - 1) * limit
        finish = start + limit

        if not limit or limit > MAX_FEED_ITEMS:
            limit = MAX_FEED_ITEMS

        if self.locale:
            items = items.filter(document__locale=self.locale)

        # Temporarily storing the selected revision PKs in a list
        # to speed up retrieval (max MAX_FEED_ITEMS size)
        item_pks = (items.order_by('-created')
                         .values_list('pk', flat=True)[start:finish])
        return (Revision.objects.filter(pk__in=list(item_pks))
                                .prefetch_related('creator',
                                                  'document'))

    def item_title(self, item):
        return '%s (%s)' % (item.document.slug, item.document.locale)

    def item_description(self, item):
        # TODO: put this in a jinja template if django syndication will let us
        previous = item.get_previous()
        if previous is None:
            action = u'Created'
        else:
            action = u'Edited'

        by = u'<h3>%s by:</h3><p>%s</p>' % (action, item.creator.username)

        if item.comment:
            comment = u'<h3>Comment:</h3><p>%s</p>' % item.comment
        else:
            comment = u''

        review_diff = u''
        tag_diff = u''
        content_diff = u''

        if previous:
            prev_review_tags = previous.review_tags.values_list('name',
                                                                flat=True)
            curr_review_tags = item.review_tags.values_list('name', flat=True)
            if set(prev_review_tags) != set(curr_review_tags):
                table = tag_diff_table(u','.join(prev_review_tags),
                                       u','.join(curr_review_tags),
                                       previous.id, item.id)
                review_diff = u'<h3>Review changes:</h3>%s' % table
                review_diff = colorize_diff(review_diff)

            if previous.tags != item.tags:
                table = tag_diff_table(previous.tags, item.tags,
                                       previous.id, item.id)
                tag_diff = u'<h3>Tag changes:</h3>%s' % table
                tag_diff = colorize_diff(tag_diff)

        previous_content = ''
        previous_id = u'N/A'
        content_diff = u'<h3>Content changes:</h3>'
        if previous:
            previous_content = previous.content
            previous_id = previous.id
            if previous_content != item.content:
                content_diff = content_diff + diff_table(
                    previous_content, item.content, previous_id, item.id)
                content_diff = colorize_diff(content_diff)
        else:
            content_diff = content_diff + escape(item.content)

        link_cell = u'<td><a href="%s">%s</a></td>'
        view_cell = link_cell % (reverse('wiki.document',
                                         args=[item.document.slug]),
                                 _('View Page'))
        edit_cell = link_cell % (reverse('wiki.edit_document',
                                         args=[item.document.slug]),
                                 _('Edit Page'))
        if previous:
            compare_cell = link_cell % (reverse('wiki.compare_revisions',
                                                args=[item.document.slug])
                                        + '?' +
                                        urllib.urlencode({'from': previous.id,
                                                          'to': item.id}),
                                        _('Show comparison'))
        else:
            compare_cell = ''
        history_cell = link_cell % (reverse('wiki.document_revisions',
                                            args=[item.document.slug]),
                                    _('History'))
        links_table = u'<table border="0" width="80%">'
        links_table = links_table + u'<tr>%s%s%s%s</tr>' % (view_cell,
                                                            edit_cell,
                                                            compare_cell,
                                                            history_cell)
        links_table = links_table + u'</table>'
        return u''.join([by, comment,
                         tag_diff, review_diff, content_diff, links_table])

    def item_link(self, item):
        return self.request.build_absolute_uri(item.document.get_absolute_url())

    def item_pubdate(self, item):
        return item.created

    def item_author_name(self, item):
        return item.creator.username

    def item_author_link(self, item):
        return self.request.build_absolute_uri(item.creator.get_absolute_url())

    def item_categories(self, item):
        return []
