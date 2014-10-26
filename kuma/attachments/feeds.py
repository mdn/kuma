from django.utils.translation import ugettext as _

from kuma.wiki.feeds import DocumentsFeed

from .models import AttachmentRevision


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
        return self.request.build_absolute_uri(item.creator.get_absolute_url())

    def item_categories(self, item):
        return []
