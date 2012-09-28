import logging
import logging.handlers

import celery.conf
import celery.log

from django.conf import settings


log = logging.getLogger('mdn')

level = settings.LOG_LEVEL

fmt = ('%s: %%(asctime)s %%(name)s:%%(levelname)s %%(message)s '
       ':%%(pathname)s:%%(lineno)s' % settings.SYSLOG_TAG)
fmt = getattr(settings, 'LOG_FORMAT', fmt)
formatter = logging.Formatter(fmt)
SysLogger = logging.handlers.SysLogHandler

handler = SysLogger(facility=SysLogger.LOG_LOCAL7)

if settings.DEBUG:
    handler = logging.StreamHandler()
    formatter = logging.Formatter(fmt, datefmt='%H:%M:%S')
if getattr(settings, 'ARECIBO_SERVER_URL', ''):
    from funfactory.log import AreciboHandler
    handler = AreciboHandler()
    level = logging.ERROR

log.setLevel(level)
handler.setLevel(level)
handler.setFormatter(formatter)
log.addHandler(handler)

if not settings.DEBUG:
    task_log = logging.getLogger('mdn.celery')
    task_proxy = celery.log.LoggingProxy(task_log)
    celery.conf.CELERYD_LOG_FILE = task_proxy
    celery.conf.CELERYD_LOG_COLOR = False
