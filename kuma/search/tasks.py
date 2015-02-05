import logging
import warnings

from django.conf import settings
from django.core.mail import mail_admins

from celery.exceptions import SoftTimeLimitExceeded
from celery.task import task


log = logging.getLogger('kuma.search.tasks')


# ignore a deprecation warning from elasticutils until the fix is released
# refs https://github.com/mozilla/elasticutils/pull/160
warnings.filterwarnings('ignore',
                        category=DeprecationWarning,
                        module='celery.decorators')

FIVE_MINUTES = 60 * 5
ONE_HOUR = FIVE_MINUTES * 12


@task(soft_time_limit=ONE_HOUR, time_limit=ONE_HOUR + FIVE_MINUTES)
def populate_index(index_pk):
    from kuma.wiki.search import WikiDocumentType
    from kuma.search.models import Index

    index = Index.objects.get(pk=index_pk)
    try:
        WikiDocumentType.reindex_all(index=index, chunk_size=500)
    except SoftTimeLimitExceeded:
        subject = ('[%s] Exceptions raised in populate_index() task '
                  'with index %s' % (settings.PLATFORM_NAME,
                                     index.prefixed_name))
        message = ("Task ran longer than soft limit of %s seconds. "
                   "Needs increasing?" % ONE_HOUR)
    else:
        index.populated = True
        index.save()
        subject = ('[%s] Index %s completely populated' %
                   (settings.PLATFORM_NAME, index.prefixed_name))
        message = "You may want to promote it now via the admin interface."
    mail_admins(subject=subject, message=message)
