import logging

from urlobject import URLObject

from django.conf import settings
from django.contrib.sites.models import Site
from django.core.mail import EmailMessage
from django.template import Context, loader

from tower import ugettext as _

from devmo import email_utils
from tidings.events import InstanceEvent
from sumo.urlresolvers import reverse
from wiki.helpers import revisions_unified_diff
from wiki.models import Document


log = logging.getLogger('mdn.wiki.events')


EMAIL_URL_TRACKING_PARAMS = {
    'utm_source': 'Notification',
    'utm_medium': 'email',
    'utm_campaign': 'Wiki Doc Edits'
}


def context_dict(revision):
    """Return a dict that fills in the blanks in notification templates."""
    document = revision.document
    from_revision = revision.get_previous()
    to_revision = revision
    diff = revisions_unified_diff(from_revision, to_revision)

    compare_url = ''
    if from_revision:
        compare_url = (reverse('wiki.compare_revisions',
            args=[document.full_path], locale=document.locale)
            + '?from=%s&to=%s' % (from_revision.id, to_revision.id))

    link_urls = {
        'compare_url': compare_url,
        'view_url': reverse('wiki.document',
                            locale=document.locale,
                            args=[document.slug]),
        'edit_url': reverse('wiki.edit_document',
                            locale=document.locale,
                            args=[document.slug]),
        'history_url': reverse('wiki.document_revisions',
                               locale=document.locale,
                               args=[document.slug]),
    }

    for name, url in link_urls.iteritems():
        url_obj = URLObject(url).add_query_params(EMAIL_URL_TRACKING_PARAMS)
        link_urls[name] = str(url_obj)

    context = {
        'document_title': document.title,
        'creator': revision.creator,
        'host': Site.objects.get_current().domain,
        'diff': diff
    }
    context.update(link_urls)

    return context


def notification_mails(revision, subject, template, url, users_and_watches):
    """Return EmailMessages in standard notification mail format."""
    document = revision.document
    subject = subject.format(title=document.title, creator=revision.creator,
                             locale=document.locale)
    t = loader.get_template(template)
    c = {'document_title': document.title,
         'creator': revision.creator,
         'url': url,
         'host': Site.objects.get_current().domain}
    content = t.render(Context(c))
    mail = EmailMessage(subject, content, settings.TIDINGS_FROM_ADDRESS)

    for u, dummy in users_and_watches:
        mail.to = [u.email]
        yield mail


class EditDocumentEvent(InstanceEvent):
    """Event fired when a certain document is edited"""
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

        return email_utils.emails_with_users_and_watches(
            subject=subject,
            text_template='wiki/email/edited.ltxt',
            html_template=None,
            context_vars=context,
            users_and_watches=users_and_watches,
            default_locale=document.locale)
