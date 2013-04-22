import logging
import os
import socket
import StringIO
import time

from django.conf import settings
from django.core.cache import cache, parse_backend_uri
from django.http import (HttpResponsePermanentRedirect, HttpResponseRedirect,
                         HttpResponse)
from django.views.decorators.cache import never_cache

import celery.task
import jingo
from PIL import Image

from sumo.urlresolvers import reverse


log = logging.getLogger('k.services')


def handle403(request):
    """A 403 message that looks nicer than the normal Apache forbidden page."""

    return jingo.render(request, 'handlers/403.html', status=403)


def handle404(request):
    """A handler for 404s."""

    return jingo.render(request, 'handlers/404.html', status=404)


def handle500(request):
    """A 500 message that looks nicer than the normal Apache error page."""

    return jingo.render(request, 'handlers/500.html', status=500)


def redirect_to(request, url, permanent=True, **kwargs):
    """Like Django's redirect_to except that 'url' is passed to reverse."""
    dest = reverse(url, kwargs=kwargs)
    if permanent:
        return HttpResponsePermanentRedirect(dest)

    return HttpResponseRedirect(dest)


def robots(request):
    """Generate a robots.txt."""
    if not settings.ENGAGE_ROBOTS:
        template = 'Disallow: /'
    else:
        template = jingo.render(request, 'sumo/robots.html')
    return HttpResponse(template, mimetype='text/plain')


@never_cache
def monitor(request):

    # For each check, a boolean pass/fail to show in the template.
    status_summary = {}
    status = 200

    # Check all memcached servers.
    scheme, servers, _ = parse_backend_uri(settings.CACHE_BACKEND)
    memcache_results = []
    status_summary['memcache'] = True
    if 'memcached' in scheme:
        hosts = servers.split(';')
        for host in hosts:
            ip, port = host.split(':')
            try:
                s = socket.socket()
                s.connect((ip, int(port)))
            except Exception, e:
                result = False
                status_summary['memcache'] = False
                log.critical('Failed to connect to memcached (%s): %s' %
                                                                    (host, e))
            else:
                result = True
            finally:
                s.close()

            memcache_results.append((ip, port, result))
        if len(memcache_results) < 2:
            status_summary['memcache'] = False
            log.warning('You should have 2+ memcache servers.  You have %s.' %
                                                        len(memcache_results))
    if not memcache_results:
        status_summary['memcache'] = False
        log.warning('Memcache is not configured.')


    # Check Libraries and versions
    libraries_results = []
    status_summary['libraries'] = True
    try:
        Image.new('RGB', (16, 16)).save(StringIO.StringIO(), 'JPEG')
        libraries_results.append(('PIL+JPEG', True, 'Got it!'))
    except Exception, e:
        status_summary['libraries'] = False
        msg = "Failed to create a jpeg image: %s" % e
        libraries_results.append(('PIL+JPEG', False, msg))


    msg = 'We want read + write.'
    filepaths = (
        (settings.USER_AVATAR_PATH, os.R_OK | os.W_OK, msg),
        (settings.IMAGE_UPLOAD_PATH, os.R_OK | os.W_OK, msg),
        (settings.THUMBNAIL_UPLOAD_PATH, os.R_OK | os.W_OK, msg),
    )

    filepath_results = []
    filepath_status = True
    for path, perms, notes in filepaths:
        path = os.path.join(settings.MEDIA_ROOT, path)
        path_exists = os.path.isdir(path)
        path_perms = os.access(path, perms)
        filepath_status = filepath_status and path_exists and path_perms
        filepath_results.append((path, path_exists, path_perms, notes))

    status_summary['filepaths'] = filepath_status

    # Check Rabbit
    # start = time.time()
    # pong = celery.task.ping()
    # rabbit_results = r = {'duration': time.time() - start}
    # status_summary['rabbit'] = pong == 'pong' and r['duration'] < 1

    if not all(status_summary.values()):
        status = 500

    return jingo.render(request, 'services/monitor.html',
                        {'memcache_results': memcache_results,
                         'libraries_results': libraries_results,
                         'filepath_results': filepath_results,
                         'status_summary': status_summary},
                         status=status)
