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
def mdc_pages():
    """Grab popular pages off MDC/DekiWiki."""

    try:
        pagelist = ElementTree.parse(urllib.urlopen(
            'https://developer.mozilla.org/@api/deki/pages/popular'))
    except Exception, e:
        log.error(e)
        return

    # Grab all English entries except home pages
    # (i.e. all pages with a / in the path)
    log.debug('Grabbing list of popular pages')
    pages = [{'id': p.get('id'),
              'uri': p.find('uri.ui').text,
              'title': p.find('title').text,
              'popularity': p.find('metrics/metric.views').text} for
             p in pagelist.findall('page') if
             p.find('path').text.lower().startswith('en/')]

    for page in pages:
        # Grab content summary
        log.debug('Fetching content for page %s' % page['title'])
        try:
            content = ElementTree.parse(urllib.urlopen(
                'https://developer.mozilla.org/@api/deki/pages/'
                '%s/contents' % page['id']))
        except Exception, e:
            log.error(e)
            return
        page['content'] = truncatewords(strip_tags(content.find('body').text),
                                        100)

        # Grab last author and edit date
        log.debug('Fetching last author for page %s' % page['title'])
        try:
            content = ElementTree.parse(urllib.urlopen(
                'https://developer.mozilla.org/@api/deki/pages/'
                '%s/revisions?limit=1' % page['id']))
        except Exception, e:
            log.error(e)
            return
        page['last_author'] = content.find('page/user.author/nick').text
        page['last_edit'] = content.find('page/date.edited').text


    outputfile = os.path.join(settings.MDC_PAGES_DIR, 'popular.json')
    log.debug('Writing results to JSON file %s' % outputfile)
    json.dump(pages, open(outputfile, 'w'))

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