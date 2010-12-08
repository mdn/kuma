import logging
import logging.handlers

from django.conf import settings

import celery.log


# Loggers created under the "z" namespace, e.g. "z.caching", will inherit the
# configuration from the base z logger.
log = logging.getLogger('k')

fmt = ('%s: %%(asctime)s %%(name)s:%%(levelname)s %%(message)s '
       ':%%(pathname)s:%%(lineno)s' % settings.SYSLOG_TAG)
fmt = getattr(settings, 'LOG_FORMAT', fmt)
level = settings.LOG_LEVEL

if settings.DEBUG:
    handler = logging.StreamHandler()
    formatter = logging.Formatter(fmt, datefmt='%H:%M:%S')
else:
    SysLogger = logging.handlers.SysLogHandler
    handler = SysLogger(facility=SysLogger.LOG_LOCAL7)
    formatter = logging.Formatter(fmt)

log.setLevel(level)
handler.setLevel(level)
handler.setFormatter(formatter)
log.addHandler(handler)

if not settings.DEBUG:
    task_log = logging.getLogger('k.task')
    task_proxy = celery.log.LoggingProxy(task_log, level)
    task_format = ('%s: [%%(asctime)s: %%(levelname)s/%%(processName)s] '
                   '%%(message)s' % settings.SYSLOG_TAG)
    celery.log.setup_logger(logfile=task_proxy, loglevel=level,
                            colorize=False)
