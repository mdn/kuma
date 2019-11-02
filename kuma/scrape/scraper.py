"""Content scraper for MDN."""


import logging
import time
from collections import OrderedDict
from datetime import datetime
from math import ceil

import requests

from .sources import (
    DocumentChildrenSource, DocumentCurrentSource, DocumentHistorySource,
    DocumentMetaSource, DocumentRedirectSource, DocumentSource, LinksSource,
    RevisionSource, Source, UserSource)
from .storage import Storage

logger = logging.getLogger('kuma.scraper')


class Requester(object):
    """Request pages from a running MDN instance."""

    MAX_ATTEMPTS = 7
    TIMEOUT = 1.0

    def __init__(self, host, ssl):
        self.host = host
        self.ssl = ssl
        self._session = None
        scheme = 'https' if ssl else 'http'
        self.base_url = '%s://%s' % (scheme, host)

    @property
    def session(self):
        if not self._session:
            self._session = requests.Session()
        return self._session

    def request(self, path, raise_for_status=True, method='GET'):
        url = self.base_url + path
        logger.debug("%s %s", method, url)
        attempts = 0
        response = None
        retry = True
        timeout = self.TIMEOUT
        while retry and 0 <= attempts < self.MAX_ATTEMPTS:
            attempts += 1
            error = None
            retry = False
            request_function = getattr(self.session, method.lower())
            try:
                response = request_function(url, timeout=timeout)
            except requests.exceptions.Timeout as err:
                logger.warn("Timeout on request %d for %s", attempts, url)
                time.sleep(timeout)
                timeout *= 2
                error = err
            except requests.exceptions.ConnectionError as err:
                logger.warn("Error request %d for %s: %s", attempts, url, err)
                error = err
            if response is None:
                if attempts >= self.MAX_ATTEMPTS:
                    raise error
                else:
                    retry = True
            elif response.status_code == 429:
                retry = True
                pause_raw = response.headers.get('retry-after', 30)
                try:
                    pause = max(1, int(pause_raw))
                except ValueError:
                    pause = 30
                logger.warn(("Request limit (429) returned for %s."
                             " Pausing for %d seconds."), url, pause)
                time.sleep(pause)
            elif response.status_code == 504:
                retry = True
                logger.warn("Gateway timeout (504) returned for %s.", url)
                time.sleep(timeout)
                timeout *= 2

        assert response is not None
        if raise_for_status:
            response.raise_for_status()
        return response


class Scraper(object):
    """Scrape data from a running MDN instance."""

    source_types = {
        'document': DocumentSource,
        'document_children': DocumentChildrenSource,
        'document_current': DocumentCurrentSource,
        'document_history': DocumentHistorySource,
        'document_meta': DocumentMetaSource,
        'document_redirect': DocumentRedirectSource,
        'links': LinksSource,
        'revision': RevisionSource,
        'user': UserSource,
    }

    def __init__(self, host='wiki.developer.mozilla.org', ssl=True):
        """Initialize Scraper."""
        self.requester = Requester(host, ssl)
        self.sources = OrderedDict()
        self.storage = Storage()
        self.defaults = {}
        self.overrides = {}

    def add_source(self, source_type, source_param='', **options):
        """Add a source of MDN data."""
        source_key = "%s:%s" % (source_type, source_param)
        if source_key in self.sources:
            changes = self.sources[source_key].merge_options(**options)
            if changes:
                logger.debug('Updating source "%s" with options %s',
                             source_key, changes)
                return True
            else:
                return False
        else:
            logger.debug('Adding source "%s" with options %s', source_key, options)
            source_options = self.defaults.get(source_type, {})
            source_options.update(options)
            source = self.create_source(source_key, **source_options)
            self.sources[source_key] = source
            return True

    def create_source(self, source_key, **options):
        source_type, source_param = source_key.split(':', 1)
        return self.source_types[source_type](source_param, **options)

    # Scrape progress report patterns
    _report_prefix = ('Round %(cycle)d, Source %(source_num)d of'
                      ' %(source_total)d: %(source_key)s ')
    _report_done = (_report_prefix +
                    'complete, freshness=%(freshness)s, with %(dep_count)s'
                    ' dependent source%(dep_s)s.')
    _report_error = (_report_prefix +
                     'errored %(err_msg)s, with %(dep_count)s dependent'
                     ' source%(dep_s)s.')
    _report_progress = (_report_prefix +
                        'in state "%(state)s" with %(dep_count)s dependent'
                        ' source%(dep_s)s.')

    def scrape(self):
        """Scrape data from MDN sources."""
        if not self.sources:
            logger.warn("No sources to scrape.")
            return self.sources
        first = True     # Always run it once
        repeat = False   # Run another round if there are new sources to scrape
        blocked = False  # Stop if we're stuck on a blocked dependency
        cycle = 0
        start = datetime.now()
        state_counts = OrderedDict((state, 0) for state in Source.STATES)
        state_counts[Source.STATE_INIT] = len(self.sources)
        while (first or repeat) and not blocked:
            first = False
            repeat = False
            source_total = (len(self.sources) -
                            state_counts[Source.STATE_DONE] -
                            state_counts[Source.STATE_ERROR])
            last_counts = state_counts
            state_counts = OrderedDict((state, 0) for state in Source.STATES)
            new_sources = []
            cycle += 1

            # Iterate over existing sources, starting with new dependencies
            source_num = 0
            for source_key, source in reversed(self.sources.items()):

                # If terminal condition, no processing to do
                if source.state in (Source.STATE_DONE, Source.STATE_ERROR):
                    state_counts[source.state] += 1
                    continue

                # Gather dependent sources
                source_num += 1
                dependencies = source.gather(self.requester, self.storage)
                new_sources.extend(dependencies)
                dep_count = len(dependencies)
                state_counts[source.state] += 1
                for dep in dependencies:
                    if "%" in dep[1]:
                        logger.warn('Source "%s" has a percent in deps',
                                    source_key)

                # Detect unfinished work and report on changed state (in debug)
                log_func = logger.debug
                err_msg = ""
                if source.state == Source.STATE_DONE:
                    log_fmt = self._report_done
                elif source.state == Source.STATE_ERROR:
                    log_func = logger.warn
                    err_msg = '"%s"' % source.error
                    log_fmt = self._report_error
                else:
                    repeat = True
                    log_fmt = self._report_progress
                log_func(log_fmt, {'cycle': cycle,
                                   'source_num': source_num,
                                   'source_total': source_total,
                                   'source_key': source_key,
                                   'err_msg': err_msg,
                                   'state': source.state,
                                   'freshness': source.freshness,
                                   'dep_count': dep_count,
                                   'dep_s': '' if dep_count == 1 else 's'})
                if source.state not in (Source.STATE_DONE, Source.STATE_ERROR):
                    for num, dep in enumerate(dependencies):
                        logger.debug('* Dep %d: %s', num + 1, dep)

            # Add new sources
            repeat = repeat or bool(new_sources)
            for source_type, source_param, options in new_sources:
                if self.add_source(source_type, source_param, **options):
                    state_counts[Source.STATE_INIT] += 1

            logger.info('Scrape progress, cycle %d: %s',
                        cycle,
                        ", ".join(("%d %s" % (v, k)
                                   for k, v in state_counts.items()
                                   if v > 0)))
            if last_counts == state_counts:
                # It looks like nothing changed state this round, so we have
                # a blocked dependency and won't finish.
                blocked = True
        duration = int(ceil((datetime.now() - start).total_seconds()))
        if blocked:
            logger.warn('Dependency block detected. Aborting after %d'
                        ' second%s.', duration, '' if duration == 1 else 's')
        else:
            logger.info('Scrape complete in %d second%s.',
                        duration, '' if duration == 1 else 's')
        return self.sources
