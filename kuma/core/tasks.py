from celery.task import task

from django.db import connection
from django.contrib.sessions.models import Session
from django.utils import timezone

from constance import config

from .cache import memcache
from .models import IPBan
from kuma.core.decorators import skip_in_maintenance_mode


LOCK_ID = 'clean-sessions-lock'
LOCK_EXPIRE = 60 * 5


def get_expired_sessions(now):
    return (Session.objects.filter(expire_date__lt=now)
                           .order_by('expire_date'))


@task
@skip_in_maintenance_mode
def clean_sessions():
    """
    Queue deleting expired session items without breaking poor MySQL
    """
    now = timezone.now()
    logger = clean_sessions.get_logger()
    chunk_size = config.SESSION_CLEANUP_CHUNK_SIZE

    if memcache.add(LOCK_ID, now.strftime('%c'), LOCK_EXPIRE):
        total_count = get_expired_sessions(now).count()
        delete_count = 0
        logger.info('Deleting the %s of %s oldest expired sessions' %
                    (chunk_size, total_count))
        try:
            cursor = connection.cursor()
            delete_count = cursor.execute("""
                DELETE
                FROM django_session
                WHERE expire_date < NOW()
                ORDER BY expire_date ASC
                LIMIT %s;
                """, [chunk_size])
        finally:
            logger.info('Deleted %s expired sessions' % delete_count)
            memcache.delete(LOCK_ID)
            expired_sessions = get_expired_sessions(now)
            if expired_sessions.exists():
                clean_sessions.apply_async()
    else:
        logger.error('The clean_sessions task is already running since %s' %
                     memcache.get(LOCK_ID))


@task
@skip_in_maintenance_mode
def delete_old_ip_bans(days=30):
    IPBan.objects.delete_old(days=days)
