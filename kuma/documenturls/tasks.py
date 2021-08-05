import datetime

from celery.task import task
from django.conf import settings
from django.utils import timezone

from kuma.core.decorators import skip_in_maintenance_mode
from kuma.documenturls.models import DocumentURL, refresh


@task
@skip_in_maintenance_mode
def refresh_documenturls():
    old = timezone.now() - datetime.timedelta(
        seconds=settings.REFRESH_DOCUMENTURLS_MIN_AGE_SECONDS
    )
    due = DocumentURL.objects.filter(modified__lt=old)
    limit = settings.REFRESH_DOCUMENTURLS_LIMIT
    # Oldest first
    for documenturl in due.order_by("modified")[:limit]:
        refresh(documenturl)
