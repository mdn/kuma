#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'Alberto Paro'

#--- Facet
class FacetFactory(object):
    def __init__(self):
        self.facets = []

    def add_term_facet(self, *args, **kwargs):
        """Add a term factory"""
        self.facets.append(TermFacet(*args, **kwargs))

    @property
    def q(self):
        res = {}
        for facet in self.facets:
            res.update(facet.serialize())
        return {"facets":res}

class Facet(object):
    def __init__(self, *args, **kwargs):
        pass

class QueryFacet(Facet):
    _internal_name = "query"

    def __init__(self, name, query, **kwargs):
        super(QueryFacet, self).__init__(**kwargs)
        self.name = name
        self.query = query

    def serialize(self):
        return {self.name:{self._internal_name:self.query.serialize()}}

class FilterFacet(Facet):
    _internal_name = "filter"

    def __init__(self, name, query, **kwargs):
        super(FilterFacet, self).__init__(**kwargs)
        self.name = name
        self.query = query

    def serialize(self):
        return {self.name:{self._internal_name:self.query.serialize()}}

class HistogramFacet(Facet):
    _internal_name = "histogram"

    def __init__(self, name,
                 field=None, interval=None, time_interval=None,
                 key_field=None, value_field=None,
                 key_script=None, value_script=None, params=None,
                 **kwargs):
        super(HistogramFacet, self).__init__(**kwargs)
        self.name = name
        self.field = field
        self.interval = interval
        self.time_interval = time_interval
        self.key_field = key_field
        self.value_field = value_field
        self.key_script = key_script
        self.value_script = value_script
        self.params = params

    def _add_interval(self, data):
        if self.interval:
            data['interval'] = self.interval
        elif self.time_interval:
            data['time_interval'] = self.time_interval
        else:
            raise RuntimeError("Invalid field: interval or time_interval required")

    def serialize(self):
        data = {}

        if self.field:
            data['field'] = self.field
            self._add_interval(data)
        elif self.key_field:
            data['key_field'] = self.key_field
            if self.value_field:
                data['value_field'] = self.value_field
            else:
                raise RuntimeError("Invalid key_field: value_field required")
            self._add_interval(data)
        elif self.key_script:
            data['key_script'] = self.key_script
            if self.value_script:
                data['value_script'] = self.value_script
            else:
                raise RuntimeError("Invalid key_script: value_script required")
            if self.params:
                data['params'] = self.params

        return {self.name:{self._internal_name:data}}

class DateHistogramFacet(Facet):
    _internal_name = "date_histogram"

    def __init__(self, name,
                 field=None, interval=None, zone=None,
                 key_field=None, value_field=None,
                 value_script=None, params=None,
                 **kwargs):
        super(DateHistogramFacet, self).__init__(**kwargs)
        self.name = name
        self.field = field
        self.interval = interval
        self.zone = zone
        self.key_field = key_field
        self.value_field = value_field
        self.value_script = value_script
        self.params = params

    def serialize(self):
        data = {}

        if self.interval:
            data['interval'] = self.interval
            if self.zone:
                data['zone'] = self.zone
        else:
            raise RuntimeError("interval required")
        if self.field:
            data['field'] = self.field
        elif self.key_field:
            data['key_field'] = self.key_field
            if self.value_field:
                data['value_field'] = self.value_field
            elif self.value_script:
                data['value_script'] = self.value_script
                if self.params:
                    data['params'] = self.params
            else:
                raise RuntimeError("Invalid key_field: value_field or value_script required")

        return {self.name:{self._internal_name:data}}

class RangeFacet(Facet):
    _internal_name = "range"

    def __init__(self, name,
                 field=None, ranges=None,
                 key_field=None, value_field=None,
                 key_script=None, value_script=None, params=None,
                 **kwargs):
        super(RangeFacet, self).__init__(**kwargs)
        self.name = name
        self.field = field
        if ranges is None:
            ranges = []
        self.ranges = ranges
        self.key_field = key_field
        self.value_field = value_field
        self.key_script = key_script
        self.value_script = value_script
        self.params = params

    def serialize(self):
        data = {}

        if not self.ranges:
            raise RuntimeError("Invalid ranges")
        data['ranges'] = self.ranges

        if self.field:
            data['field'] = self.field
        elif self.key_field:
            data['key_field'] = self.key_field
            if self.value_field:
                data['value_field'] = self.value_field
            else:
                raise RuntimeError("Invalid key_field: value_field required")
        elif self.key_script:
            data['key_script'] = self.key_script
            if self.value_script:
                data['value_script'] = self.value_script
            else:
                raise RuntimeError("Invalid key_script: value_script required")
            if self.params:
                data['params'] = self.params

        return {self.name:{self._internal_name:data}}

class StatisticalFacet(Facet):
    _internal_name = "statistical"

    def __init__(self, name, field=None, script=None, params=None, **kwargs):
        super(StatisticalFacet, self).__init__(**kwargs)
        self.name = name
        self.field = field
        self.script = script
        self.params = params

    def serialize(self):
        data = {}

        if self.field:
            data['field'] = self.field
        elif self.script:
            data['script'] = self.script
            if self.params:
                data['params'] = self.params

        return {self.name:{self._internal_name:data}}

class TermFacet(Facet):
    _internal_name = "terms"

    def __init__(self, field=None, fields=None, name=None, size=10,
                 order=None, exclude=None,
                 regex=None, regex_flags="DOTALL",
                 script=None, **kwargs):
        super(TermFacet, self).__init__(**kwargs)
        self.name = name
        self.field = field
        self.fields = fields
        if name is None:
            self.name = field
        self.size = size
        self.order = order
        self.exclude = exclude or []
        self.regex = regex
        self.regex_flags = regex_flags
        self.script = script

    def serialize(self):
        if self.fields:
            data = {'fields':self.fields}
        else:
            if self.field:
                data = {'field':self.field}
            else:
                raise RuntimeError("Field or Fields is required:%s" % self.order)

        if self.size:
            data['size'] = self.size

        if self.order:
            if self.order not in ['count', 'term', 'reverse_count', 'reverse_term']:
                raise RuntimeError("Invalid order value:%s" % self.order)
            data['order'] = self.order
        if self.exclude:
            data['exclude'] = self.exclude
        if self.regex:
            data['regex'] = self.regex
            if self.regex_flags:
                data['regex_flags'] = self.regex_flags
        elif self.script:
            data['script'] = self.script

        return {self.name:{self._internal_name:data}}
