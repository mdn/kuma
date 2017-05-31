"""Content scraper for MDN."""
from __future__ import unicode_literals

from collections import OrderedDict
import logging
import time

import requests

from .sources import Source, UserSource
from .storage import Storage

logger = logging.getLogger('kuma.scraper')


class Requester(object):
    """Request pages from a running MDN instance."""

    MAX_ATTEMPTS = 3
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

    def request(self, path, raise_for_status=True):
        url = self.base_url + path
        logger.debug("GET %s", url)
        attempts = 0
        response = None
        timeout = self.TIMEOUT
        while response is None and 0 <= attempts < self.MAX_ATTEMPTS:
            attempts += 1
            err = None
            try:
                response = self.session.get(url, timeout=timeout)
            except requests.exceptions.Timeout as err:
                logger.warn("Timeout on request %d for %s", attempts, url)
                time.sleep(timeout)
                timeout *= 2
            except requests.exceptions.ConnectionError as err:
                logger.warn("Error request %d for %s: %s", attempts, url, err)
            if response is None and attempts >= self.MAX_ATTEMPTS:
                raise err

        assert response is not None
        if raise_for_status:
            response.raise_for_status()
        return response


class Scraper(object):
    """Scrape data from a running MDN instance."""

    source_types = {
        'user': UserSource,
    }

    def __init__(self, host='developer.mozilla.org', ssl=True):
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

    def scrape(self):
        """Scrape data from MDN sources."""
        if not self.sources:
            logger.warn("No sources to scrape.")
            return self.sources
        first = True
        repeat = False
        cycle = 0
        state_counts = OrderedDict((state, 0) for state in Source.STATES)
        state_counts[Source.STATE_INIT] = len(self.sources)
        while first or repeat:
            first = False
            repeat = False
            source_total = (len(self.sources) -
                            state_counts[Source.STATE_DONE] -
                            state_counts[Source.STATE_ERROR])
            last_counts = state_counts
            state_counts = OrderedDict((state, 0) for state in Source.STATES)
            new_sources = []
            cycle += 1

            # Iterate over existing sources
            source_num = 0
            for source_key, source in self.sources.items():

                # If terminal condition, no processing to do
                if source.state in (Source.STATE_DONE, Source.STATE_ERROR):
                    state_counts[source.state] += 1
                    continue

                # Gather dependent sources
                source_num += 1
                old_state = source.state
                dependencies = source.gather(self.requester, self.storage)
                new_sources.extend(dependencies)
                dep_count = len(dependencies)
                state_counts[source.state] += 1
                for dep in dependencies:
                    if "%" in dep[1]:
                        logger.warn('Source "%s" has a percent in deps',
                                    source_key)

                # At verbosity=debug, report on changed state
                if source.state not in (Source.STATE_DONE, Source.STATE_ERROR):
                    repeat = True
                    logger.debug('%d:%d/%d Source "%s" in state "%s" with %d'
                                 ' dependant source%s.',
                                 cycle, source_num, source_total,
                                 source_key, source.state, dep_count,
                                 '' if dep_count == 1 else 's')
                    for num, dep in enumerate(dependencies):
                        logger.debug('* Dep %d: %s', num + 1, dep)
                else:
                    assert old_state != Source.STATE_DONE
                    logger.debug('%d:%d/%d Source "%s" complete, '
                                 'freshness=%s, with %d dependant source%s.',
                                 cycle, source_num, source_total,
                                 source_key, source.freshness, dep_count,
                                 '' if dep_count == 1 else 's')

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
                logger.warn("Dependency block detected. Aborting.")
                return self.sources
        logger.info('Scrape complete.')
        return self.sources
