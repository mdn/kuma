#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2007 Edgewall Software
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution. The terms
# are also available at http://babel.edgewall.org/wiki/License.
#
# This software consists of voluntary contributions made by many
# individuals. For the exact contribution history, see the revision
# history and logs, available at http://babel.edgewall.org/log/.

import copy
from optparse import OptionParser
import os
import pickle
import re
import sys
try:
    from xml.etree.ElementTree import parse
except ImportError:
    from elementtree.ElementTree import parse

# Make sure we're using Babel source, and not some previously installed version
sys.path.insert(0, os.path.join(os.path.dirname(sys.argv[0]), '..'))

from babel import dates, numbers
from babel.localedata import Alias

weekdays = {'mon': 0, 'tue': 1, 'wed': 2, 'thu': 3, 'fri': 4, 'sat': 5,
            'sun': 6}

try:
    any
except NameError:
    def any(iterable):
        return filter(None, list(iterable))


def _text(elem):
    buf = [elem.text or '']
    for child in elem:
        buf.append(_text(child))
    buf.append(elem.tail or '')
    return u''.join(filter(None, buf)).strip()


NAME_RE = re.compile(r"^\w+$")
TYPE_ATTR_RE = re.compile(r"^\w+\[@type='(.*?)'\]$")

NAME_MAP = {
    'dateFormats': 'date_formats',
    'dateTimeFormats': 'datetime_formats',
    'eraAbbr': 'abbreviated',
    'eraNames': 'wide',
    'eraNarrow': 'narrow',
    'timeFormats': 'time_formats'
}

def _translate_alias(ctxt, path):
    parts = path.split('/')
    keys = ctxt[:]
    for part in parts:
        if part == '..':
            keys.pop()
        else:
            match = TYPE_ATTR_RE.match(part)
            if match:
                keys.append(match.group(1))
            else:
                assert NAME_RE.match(part)
                keys.append(NAME_MAP.get(part, part))
    return keys


def main():
    parser = OptionParser(usage='%prog path/to/cldr')
    options, args = parser.parse_args()
    if len(args) != 1:
        parser.error('incorrect number of arguments')

    srcdir = args[0]
    destdir = os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])),
                           '..', 'babel')

    sup = parse(os.path.join(srcdir, 'supplemental', 'supplementalData.xml'))

    # Import global data from the supplemental files
    global_data = {}

    territory_zones = global_data.setdefault('territory_zones', {})
    zone_aliases = global_data.setdefault('zone_aliases', {})
    zone_territories = global_data.setdefault('zone_territories', {})
    for elem in sup.findall('//timezoneData/zoneFormatting/zoneItem'):
        tzid = elem.attrib['type']
        territory_zones.setdefault(elem.attrib['territory'], []).append(tzid)
        zone_territories[tzid] = elem.attrib['territory']
        if 'aliases' in elem.attrib:
            for alias in elem.attrib['aliases'].split():
                zone_aliases[alias] = tzid

    # Import Metazone mapping
    meta_zones = global_data.setdefault('meta_zones', {})
    tzsup = parse(os.path.join(srcdir, 'supplemental', 'metazoneInfo.xml'))
    for elem in tzsup.findall('//timezone'):
        for child in elem.findall('usesMetazone'):
            if 'to' not in child.attrib: # FIXME: support old mappings
                meta_zones[elem.attrib['type']] = child.attrib['mzone']

    outfile = open(os.path.join(destdir, 'global.dat'), 'wb')
    try:
        pickle.dump(global_data, outfile, 2)
    finally:
        outfile.close()

    # build a territory containment mapping for inheritance
    regions = {}
    for elem in sup.findall('//territoryContainment/group'):
        regions[elem.attrib['type']] = elem.attrib['contains'].split()

    # Resolve territory containment
    territory_containment = {}
    region_items = regions.items()
    region_items.sort()
    for group, territory_list in region_items:
        for territory in territory_list:
            containers = territory_containment.setdefault(territory, set([]))
            if group in territory_containment:
                containers |= territory_containment[group]
            containers.add(group)

    filenames = os.listdir(os.path.join(srcdir, 'main'))
    filenames.remove('root.xml')
    filenames.sort(lambda a,b: len(a)-len(b))
    filenames.insert(0, 'root.xml')

    for filename in filenames:
        stem, ext = os.path.splitext(filename)
        if ext != '.xml':
            continue

        print>>sys.stderr, 'Processing input file %r' % filename
        tree = parse(os.path.join(srcdir, 'main', filename))
        data = {}

        language = None
        elem = tree.find('//identity/language')
        if elem is not None:
            language = elem.attrib['type']
        print>>sys.stderr, '  Language:  %r' % language

        territory = None
        elem = tree.find('//identity/territory')
        if elem is not None:
            territory = elem.attrib['type']
        else:
            territory = '001' # world
        print>>sys.stderr, '  Territory: %r' % territory
        regions = territory_containment.get(territory, [])
        print>>sys.stderr, '  Regions:    %r' % regions

        # <localeDisplayNames>

        territories = data.setdefault('territories', {})
        for elem in tree.findall('//territories/territory'):
            if ('draft' in elem.attrib or 'alt' in elem.attrib) \
                    and elem.attrib['type'] in territories:
                continue
            territories[elem.attrib['type']] = _text(elem)

        languages = data.setdefault('languages', {})
        for elem in tree.findall('//languages/language'):
            if ('draft' in elem.attrib or 'alt' in elem.attrib) \
                    and elem.attrib['type'] in languages:
                continue
            languages[elem.attrib['type']] = _text(elem)

        variants = data.setdefault('variants', {})
        for elem in tree.findall('//variants/variant'):
            if ('draft' in elem.attrib or 'alt' in elem.attrib) \
                    and elem.attrib['type'] in variants:
                continue
            variants[elem.attrib['type']] = _text(elem)

        scripts = data.setdefault('scripts', {})
        for elem in tree.findall('//scripts/script'):
            if ('draft' in elem.attrib or 'alt' in elem.attrib) \
                    and elem.attrib['type'] in scripts:
                continue
            scripts[elem.attrib['type']] = _text(elem)

        # <dates>

        week_data = data.setdefault('week_data', {})
        supelem = sup.find('//weekData')

        for elem in supelem.findall('minDays'):
            territories = elem.attrib['territories'].split()
            if territory in territories or any([r in territories for r in regions]):
                week_data['min_days'] = int(elem.attrib['count'])

        for elem in supelem.findall('firstDay'):
            territories = elem.attrib['territories'].split()
            if territory in territories or any([r in territories for r in regions]):
                week_data['first_day'] = weekdays[elem.attrib['day']]

        for elem in supelem.findall('weekendStart'):
            territories = elem.attrib['territories'].split()
            if territory in territories or any([r in territories for r in regions]):
                week_data['weekend_start'] = weekdays[elem.attrib['day']]

        for elem in supelem.findall('weekendEnd'):
            territories = elem.attrib['territories'].split()
            if territory in territories or any([r in territories for r in regions]):
                week_data['weekend_end'] = weekdays[elem.attrib['day']]

        zone_formats = data.setdefault('zone_formats', {})
        for elem in tree.findall('//timeZoneNames/gmtFormat'):
            if 'draft' not in elem.attrib and 'alt' not in elem.attrib:
                zone_formats['gmt'] = unicode(elem.text).replace('{0}', '%s')
                break
        for elem in tree.findall('//timeZoneNames/regionFormat'):
            if 'draft' not in elem.attrib and 'alt' not in elem.attrib:
                zone_formats['region'] = unicode(elem.text).replace('{0}', '%s')
                break
        for elem in tree.findall('//timeZoneNames/fallbackFormat'):
            if 'draft' not in elem.attrib and 'alt' not in elem.attrib:
                zone_formats['fallback'] = unicode(elem.text) \
                    .replace('{0}', '%(0)s').replace('{1}', '%(1)s')
                break

        time_zones = data.setdefault('time_zones', {})
        for elem in tree.findall('//timeZoneNames/zone'):
            info = {}
            city = elem.findtext('exemplarCity')
            if city:
                info['city'] = unicode(city)
            for child in elem.findall('long/*'):
                info.setdefault('long', {})[child.tag] = unicode(child.text)
            for child in elem.findall('short/*'):
                info.setdefault('short', {})[child.tag] = unicode(child.text)
            time_zones[elem.attrib['type']] = info

        meta_zones = data.setdefault('meta_zones', {})
        for elem in tree.findall('//timeZoneNames/metazone'):
            info = {}
            city = elem.findtext('exemplarCity')
            if city:
                info['city'] = unicode(city)
            for child in elem.findall('long/*'):
                info.setdefault('long', {})[child.tag] = unicode(child.text)
            for child in elem.findall('short/*'):
                info.setdefault('short', {})[child.tag] = unicode(child.text)
            info['common'] = elem.findtext('commonlyUsed') == 'true'
            meta_zones[elem.attrib['type']] = info

        for calendar in tree.findall('//calendars/calendar'):
            if calendar.attrib['type'] != 'gregorian':
                # TODO: support other calendar types
                continue

            months = data.setdefault('months', {})
            for ctxt in calendar.findall('months/monthContext'):
                ctxt_type = ctxt.attrib['type']
                ctxts = months.setdefault(ctxt_type, {})
                for width in ctxt.findall('monthWidth'):
                    width_type = width.attrib['type']
                    widths = ctxts.setdefault(width_type, {})
                    for elem in width.getiterator():
                        if elem.tag == 'month':
                            if ('draft' in elem.attrib or 'alt' in elem.attrib) \
                                    and int(elem.attrib['type']) in widths:
                                continue
                            widths[int(elem.attrib.get('type'))] = unicode(elem.text)
                        elif elem.tag == 'alias':
                            ctxts[width_type] = Alias(
                                _translate_alias(['months', ctxt_type, width_type],
                                                 elem.attrib['path'])
                            )

            days = data.setdefault('days', {})
            for ctxt in calendar.findall('days/dayContext'):
                ctxt_type = ctxt.attrib['type']
                ctxts = days.setdefault(ctxt_type, {})
                for width in ctxt.findall('dayWidth'):
                    width_type = width.attrib['type']
                    widths = ctxts.setdefault(width_type, {})
                    for elem in width.getiterator():
                        if elem.tag == 'day':
                            dtype = weekdays[elem.attrib['type']]
                            if ('draft' in elem.attrib or 'alt' not in elem.attrib) \
                                    and dtype in widths:
                                continue
                            widths[dtype] = unicode(elem.text)
                        elif elem.tag == 'alias':
                            ctxts[width_type] = Alias(
                                _translate_alias(['days', ctxt_type, width_type],
                                                 elem.attrib['path'])
                            )

            quarters = data.setdefault('quarters', {})
            for ctxt in calendar.findall('quarters/quarterContext'):
                ctxt_type = ctxt.attrib['type']
                ctxts = quarters.setdefault(ctxt.attrib['type'], {})
                for width in ctxt.findall('quarterWidth'):
                    width_type = width.attrib['type']
                    widths = ctxts.setdefault(width_type, {})
                    for elem in width.getiterator():
                        if elem.tag == 'quarter':
                            if ('draft' in elem.attrib or 'alt' in elem.attrib) \
                                    and int(elem.attrib['type']) in widths:
                                continue
                            widths[int(elem.attrib['type'])] = unicode(elem.text)
                        elif elem.tag == 'alias':
                            ctxts[width_type] = Alias(
                                _translate_alias(['quarters', ctxt_type, width_type],
                                                 elem.attrib['path'])
                            )

            eras = data.setdefault('eras', {})
            for width in calendar.findall('eras/*'):
                width_type = NAME_MAP[width.tag]
                widths = eras.setdefault(width_type, {})
                for elem in width.getiterator():
                    if elem.tag == 'era':
                        if ('draft' in elem.attrib or 'alt' in elem.attrib) \
                                and int(elem.attrib['type']) in widths:
                            continue
                        widths[int(elem.attrib.get('type'))] = unicode(elem.text)
                    elif elem.tag == 'alias':
                        eras[width_type] = Alias(
                            _translate_alias(['eras', width_type],
                                             elem.attrib['path'])
                        )

            # AM/PM
            periods = data.setdefault('periods', {})
            for elem in calendar.findall('am'):
                if ('draft' in elem.attrib or 'alt' in elem.attrib) \
                        and elem.tag in periods:
                    continue
                periods[elem.tag] = unicode(elem.text)
            for elem in calendar.findall('pm'):
                if ('draft' in elem.attrib or 'alt' in elem.attrib) \
                        and elem.tag in periods:
                    continue
                periods[elem.tag] = unicode(elem.text)

            date_formats = data.setdefault('date_formats', {})
            for format in calendar.findall('dateFormats'):
                for elem in format.getiterator():
                    if elem.tag == 'dateFormatLength':
                        if 'draft' in elem.attrib and \
                                elem.attrib.get('type') in date_formats:
                            continue
                        try:
                            date_formats[elem.attrib.get('type')] = \
                                dates.parse_pattern(unicode(elem.findtext('dateFormat/pattern')))
                        except ValueError, e:
                            print>>sys.stderr, 'ERROR: %s' % e
                    elif elem.tag == 'alias':
                        date_formats = Alias(_translate_alias(
                            ['date_formats'], elem.attrib['path'])
                        )

            time_formats = data.setdefault('time_formats', {})
            for format in calendar.findall('timeFormats'):
                for elem in format.getiterator():
                    if elem.tag == 'timeFormatLength':
                        if ('draft' in elem.attrib or 'alt' in elem.attrib) \
                                and elem.attrib.get('type') in time_formats:
                            continue
                        try:
                            time_formats[elem.attrib.get('type')] = \
                                dates.parse_pattern(unicode(elem.findtext('timeFormat/pattern')))
                        except ValueError, e:
                            print>>sys.stderr, 'ERROR: %s' % e
                    elif elem.tag == 'alias':
                        time_formats = Alias(_translate_alias(
                            ['time_formats'], elem.attrib['path'])
                        )

            datetime_formats = data.setdefault('datetime_formats', {})
            for format in calendar.findall('dateTimeFormats'):
                for elem in format.getiterator():
                    if elem.tag == 'dateTimeFormatLength':
                        if ('draft' in elem.attrib or 'alt' in elem.attrib) \
                                and elem.attrib.get('type') in datetime_formats:
                            continue
                        try:
                            datetime_formats[elem.attrib.get('type')] = \
                                unicode(elem.findtext('dateTimeFormat/pattern'))
                        except ValueError, e:
                            print>>sys.stderr, 'ERROR: %s' % e
                    elif elem.tag == 'alias':
                        datetime_formats = Alias(_translate_alias(
                            ['datetime_formats'], elem.attrib['path'])
                        )

        # <numbers>

        number_symbols = data.setdefault('number_symbols', {})
        for elem in tree.findall('//numbers/symbols/*'):
            number_symbols[elem.tag] = unicode(elem.text)

        decimal_formats = data.setdefault('decimal_formats', {})
        for elem in tree.findall('//decimalFormats/decimalFormatLength'):
            if ('draft' in elem.attrib or 'alt' in elem.attrib) \
                    and elem.attrib.get('type') in decimal_formats:
                continue
            pattern = unicode(elem.findtext('decimalFormat/pattern'))
            decimal_formats[elem.attrib.get('type')] = numbers.parse_pattern(pattern)

        scientific_formats = data.setdefault('scientific_formats', {})
        for elem in tree.findall('//scientificFormats/scientificFormatLength'):
            if ('draft' in elem.attrib or 'alt' in elem.attrib) \
                    and elem.attrib.get('type') in scientific_formats:
                continue
            pattern = unicode(elem.findtext('scientificFormat/pattern'))
            scientific_formats[elem.attrib.get('type')] = numbers.parse_pattern(pattern)

        currency_formats = data.setdefault('currency_formats', {})
        for elem in tree.findall('//currencyFormats/currencyFormatLength'):
            if ('draft' in elem.attrib or 'alt' in elem.attrib) \
                    and elem.attrib.get('type') in currency_formats:
                continue
            pattern = unicode(elem.findtext('currencyFormat/pattern'))
            currency_formats[elem.attrib.get('type')] = numbers.parse_pattern(pattern)

        percent_formats = data.setdefault('percent_formats', {})
        for elem in tree.findall('//percentFormats/percentFormatLength'):
            if ('draft' in elem.attrib or 'alt' in elem.attrib) \
                    and elem.attrib.get('type') in percent_formats:
                continue
            pattern = unicode(elem.findtext('percentFormat/pattern'))
            percent_formats[elem.attrib.get('type')] = numbers.parse_pattern(pattern)

        currency_names = data.setdefault('currency_names', {})
        currency_symbols = data.setdefault('currency_symbols', {})
        for elem in tree.findall('//currencies/currency'):
            code = elem.attrib['type']
            # TODO: support plural rules for currency name selection
            for name in elem.findall('displayName'):
                if ('draft' in name.attrib or 'count' in name.attrib) \
                        and code in currency_names:
                    continue
                currency_names[code] = unicode(name.text)
            # TODO: support choice patterns for currency symbol selection
            symbol = elem.find('symbol')
            if symbol is not None and 'draft' not in symbol.attrib \
                    and 'choice' not in symbol.attrib:
                currency_symbols[code] = unicode(symbol.text)

        outfile = open(os.path.join(destdir, 'localedata', stem + '.dat'), 'wb')
        try:
            pickle.dump(data, outfile, 2)
        finally:
            outfile.close()


if __name__ == '__main__':
    main()
