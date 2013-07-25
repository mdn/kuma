import json
import os.path
import re
import urllib
from xml.etree import ElementTree

from django.conf import settings
from django.template.defaultfilters import truncatewords
from django.utils.html import strip_tags

import commonware
import cronjobs
from dateutil.parser import parse as parse_date

from devmo.helpers import get_localized_devmo_path, check_devmo_local_page


log = commonware.log.getLogger('kuma.cron')


@cronjobs.register
def cache_doc_center_links():
    paths_completed = []
    devmo_url_regexp = "devmo_url\(_\('(?P<path>[\w/_]+)'\)\)"
    """Cache MDC/DekiWiki links for devmo_url."""
    for subdir, dirs, files in os.walk(settings.ROOT):
        for file in files:
            if file.endswith('html') and subdir.find('vendor') is -1:
                f = open(os.path.join(subdir, file), 'r')
                lines = f.readlines()
                f.close()
                for line in lines:
                    if line.find('devmo_url') is -1:
                        continue
                    m = re.search(devmo_url_regexp, line)
                    if not m:
                        continue
                    path_dict = m.groupdict()
                    path = path_dict['path']
                    for locale in settings.MDN_LANGUAGES:
                        devmo_locale, devmo_path, devmo_local_path = get_localized_devmo_path(path, locale)
                        if devmo_local_path not in paths_completed:
                            print('check_devmo_local_page(%s)' % devmo_local_path)
                            check_devmo_local_page(devmo_local_path)
                            paths_completed.append(devmo_local_path)
