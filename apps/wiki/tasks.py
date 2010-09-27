import logging

from django.contrib.sites.models import Site
from django.template import Context, loader
from django.core.mail import send_mail

from celery.decorators import task
from tower import ugettext as _

from sumo.urlresolvers import reverse


log = logging.getLogger('k.task')


@task
def send_reviewed_notification(revision, document, message):
    log.debug('Sending reviewed email for revision (id=%s)' % revision.id)
    from_address = 'notifications@support.mozilla.com'
    if revision.is_approved:
        subject = _('Your revision has been approved: %s')
    else:
        subject = _('Your revision has been rejected: %s')
    subject = subject % document.title
    t = loader.get_template('wiki/email/reviewed.ltxt')
    url = reverse('wiki.document_revisions', locale=document.locale,
                  args=[document.slug])
    content = t.render(Context({'document_title': document.title,
                                'approved': revision.is_approved,
                                'reviewer': revision.reviewer,
                                'message': message,
                                'history_url': url,
                                'host': Site.objects.get_current().domain}))
    send_mail(subject, content, from_address, [revision.creator.email])
