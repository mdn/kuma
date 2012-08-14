"""Feeds for documents"""
import datetime
import hashlib
import urllib
import validate_jsonp

import jingo

from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.syndication.views import Feed, FeedDoesNotExist
from django.shortcuts import get_object_or_404
from django.utils.feedgenerator import (SyndicationFeed, Rss201rev2Feed,
                                        Atom1Feed)
from django.utils.html import escape
import django.utils.simplejson as json
from django.utils.translation import ugettext as _

from sumo.urlresolvers import reverse
from devmo.models import UserProfile

from wiki.helpers import diff_table, diff_inline
from wiki.models import Document, Revision, AttachmentRevision


MAX_FEED_ITEMS = getattr(settings, 'MAX_FEED_ITEMS', 100)


class DocumentsFeed(Feed):
    title = _('MDN documents')
    subtitle = _('Documents authored by MDN users')
    link = _('/')

    def __call__(self, request, *args, **kwargs):
        self.request = request
        return super(DocumentsFeed, self).__call__(request, *args, **kwargs)

    def feed_extra_kwargs(self, obj):
        return {'request': self.request, }

    def item_extra_kwargs(self, obj):
        return {'obj': obj, }

    def get_object(self, request, format):
        if format == 'json':
            self.feed_type = DocumentJSONFeedGenerator
        elif format == 'rss':
            self.feed_type = Rss201rev2Feed
        else:
            self.feed_type = Atom1Feed

    def item_pubdate(self, document):
        return document.modified

    def item_title(self, document):
        return document.title

    def item_description(self, document):
        return document.current_revision.summary

    def item_author_name(self, document):
        return '%s' % document.current_revision.creator

    def item_author_link(self, document):
        return self.request.build_absolute_uri(
            reverse('devmo.views.profile_view',
                    args=(document.current_revision.creator.username,)))

    def item_link(self, document):
        return self.request.build_absolute_uri(
            reverse('wiki.views.document', locale=document.locale,
                    args=(document.slug,)))

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
            if not validate_jsonp.is_valid_jsonp_callback_value(callback):
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
            
            profile = UserProfile.objects.get(user=revision.creator)
            if hasattr(profile, 'gravatar'):
                item_out['author_avatar'] = profile.gravatar

            summary = revision.summary
            if summary:
                item_out['summary'] = summary

            # Linkify the tags used in the feed item
            categories = dict(
                (x, request.build_absolute_uri(
                        reverse('wiki.views.list_documents',
                                kwargs={'tag': x})))
                for x in item['categories']
            )
            if categories:
                item_out['categories'] = categories

            #TODO: What else might be useful in a JSON feed of documents?

            items_out.append(item_out)

        data = items_out

        if callback:
            outfile.write('%s(' % callback)
        outfile.write(json.dumps(data, default=self._encode_complex))
        if callback:
            outfile.write(')')


class DocumentsRecentFeed(DocumentsFeed):
    """Feed of recently revised documents"""

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
                reverse('wiki.views.list_documents'))

    def items(self):
        locale = ((self.request.GET.get('all_locales', False) is False)
                  and self.request.locale or None)
        return (Document.objects
                        .filter_for_list(tag_name=self.tag,
                                         category=self.category,
                                         locale=locale)
                        .filter(current_revision__isnull=False)
                        .order_by('-modified')
                        [:MAX_FEED_ITEMS])


class DocumentsReviewFeed(DocumentsRecentFeed):
    """Feed of documents in need of review"""

    def get_object(self, request, format, tag=None):
        super(DocumentsReviewFeed, self).get_object(request, format)
        self.subtitle = None
        if tag:
            self.title = _('MDN documents for %s review' % tag)
            self.link = self.request.build_absolute_uri(
                reverse('wiki.views.list_documents_for_review',
                        args=(tag,)))
        else:
            self.title = _('MDN documents for review')
            self.link = self.request.build_absolute_uri(
                reverse('wiki.views.list_documents_for_review'))
        return tag

    def items(self, tag=None):
        locale = ((self.request.GET.get('all_locales', False) is False)
                  and self.request.locale or None)
        return (Document.objects
                        .filter_for_review(tag_name=tag, locale=locale)
                        .order_by('-modified')
                        [:MAX_FEED_ITEMS])


class RevisionsFeed(DocumentsFeed):
    """Feed of recent revisions"""

    title = _("MDN recent revisions")
    subtitle = _("Recent revisions to MDN documents")

    def items(self):
        items = Revision.objects
        if self.request.GET.get('all_locales', False) is False:
            items = items.filter(document__locale=self.request.locale)
        return items.order_by('-created')[:MAX_FEED_ITEMS]

    def item_title(self, item):
        return "%s/%s" % (item.document.locale, item.document.full_path)

    def item_description(self, item):
        previous = item.get_previous()
        if previous is None:
            return '<p>Created by: %s</p>' % item.creator.username
        # TODO: put this in a jinja template if django syndication will let us
        by = '<p>Edited by: %s</p>' % item.creator.username
        comment = '<p>Comment: %s</p>' % item.comment
        diff = ("Diff:<blockquote>%s</blockquote>" % (
            diff_inline(previous.content, item.content)))

        diff = (diff.replace('<ins', '<ins style="background-color: #AAFFAA;text-decoration:none;"')
                .replace('<del', '<del style="background-color: #FFAAAA;text-decoration:none;"'))

        link_cell = '<td><a href="%s">%s</a></td>'
        view_cell = link_cell % (reverse('wiki.document',
                                         args=[item.document.full_path]),
                                 _('View Page'))
        edit_cell = link_cell % (reverse('wiki.edit_document',
                                         args=[item.document.full_path]),
                                 _('Edit Page'))
        compare_cell = link_cell % (reverse('wiki.compare_revisions',
                                         args=[item.document.full_path])
                                    + '?' +
                                    urllib.urlencode({'from': previous.id,
                                                      'to': item.id}),
                                 _('Show comparison'))
        history_cell = link_cell % (reverse('wiki.document_revisions',
                                         args=[item.document.full_path]),
                                 _('History'))
        links_table = '<table border="0" width="80%">'
        links_table = links_table + '<tr>%s%s%s%s</tr>' % (view_cell, edit_cell, compare_cell, history_cell)
        links_table = links_table + '</table>'
        description = "%s%s%s%s" % (by, comment, diff, links_table)
        return description

    def item_link(self, item):
        return reverse('wiki.document', args=[item.document.full_path])

    def item_pubdate(self, item):
        return item.created

    def item_author_name(self, item):
        return '%s' % item.creator

    def item_author_link(self, item):
        return self.request.build_absolute_uri(
            reverse('devmo.views.profile_view',
                    args=(item.creator.username,)))

    def item_categories(self, item):
        return []


class AttachmentsFeed(DocumentsFeed):
    title = _("MDN recent file changes")
    subtitle = _("Recent revisions to MDN file attachments")

    def items(self):
        return AttachmentRevision.objects.order_by('-created')[:50]

    def item_title(self, item):
        return item.title

    def item_description(self, item):
        previous = item.get_previous()
        if previous is None:
            return '<p>Created by: %s</p>' % item.creator.username
        return "<p>Edited by %s: %s" % (item.creator.username, item.comment)

    def item_link(self, item):
        return self.request.build_absolute_uri(
            item.attachment.get_absolute_url())

    def item_pubdate(self, item):
        return item.created

    def item_author_name(self, item):
        return '%s' % item.creator

    def item_author_link(self, item):
        return self.request.build_absolute_uri(
            reverse('devmo.views.profile_view',
                    args=(item.creator.username,)))

    def item_categories(self, item):
        return []
