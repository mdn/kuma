import logging

from tower import ugettext as _

from kuma.core.email_utils import emails_with_users_and_watches
from kuma.core.helpers import add_utm
from kuma.core.urlresolvers import reverse
from tidings.events import InstanceEvent

from .helpers import revisions_unified_diff
from .models import Document


log = logging.getLogger('kuma.wiki.events')


def context_dict(revision):
    """
    Return a dict that fills in the blanks in notification templates.
    """
    document = revision.document
    from_revision = revision.previous
    to_revision = revision
    diff = revisions_unified_diff(from_revision, to_revision)

    context = {
        'document_title': document.title,
        'creator': revision.creator,
        'diff': diff,
    }

    if from_revision:
        compare_url = (
            reverse('wiki.compare_revisions',
                    args=[document.slug], locale=document.locale) +
            '?from=%s&to=%s' % (from_revision.id, to_revision.id)
        )
    else:
        compare_url = ''

    link_urls = {
        'user_url': revision.creator.get_absolute_url(),
        'compare_url': compare_url,
        'view_url': document.get_absolute_url(),
        'edit_url': reverse('wiki.edit_document',
                            locale=document.locale,
                            args=[document.slug]),
        'history_url': reverse('wiki.document_revisions',
                               locale=document.locale,
                               args=[document.slug]),
    }

    for name, url in link_urls.items():
        context[name] = add_utm(url, 'Wiki Doc Edits')

    return context


class EditDocumentEvent(InstanceEvent):
    """
    Event fired when a certain document is edited
    """
    event_type = 'wiki edit document'
    content_type = Document

    def __init__(self, revision):
        super(EditDocumentEvent, self).__init__(revision.document)
        self.revision = revision

    def _mails(self, users_and_watches):
        revision = self.revision
        document = revision.document
        log.debug('Sending edited notification email for document (id=%s)' %
                  document.id)
        subject = _(u'[MDN] Page "{document_title}" changed by {creator}')
        context = context_dict(revision)

        return emails_with_users_and_watches(
            subject=subject,
            text_template='wiki/email/edited.ltxt',
            html_template=None,
            context_vars=context,
            users_and_watches=users_and_watches,
            default_locale=document.locale)
