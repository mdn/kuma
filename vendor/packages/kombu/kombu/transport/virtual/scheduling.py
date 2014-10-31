"""
    kombu.transport.virtual.scheduling
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Consumer utilities.

    :copyright: (c) 2009 - 2012 by Ask Solem.
    :license: BSD, see LICENSE for more details.

"""
from __future__ import absolute_import

from itertools import count


class FairCycle(object):
    """Consume from a set of resources, where each resource gets
    an equal chance to be consumed from."""

    def __init__(self, fun, resources, predicate=Exception):
        self.fun = fun
        self.resources = resources
        self.predicate = predicate
        self.pos = 0

    def _next(self):
        while 1:
            try:
                resource = self.resources[self.pos]
                self.pos += 1
                return resource
            except IndexError:
                self.pos = 0
                if not self.resources:
                    raise self.predicate()

    def get(self, **kwargs):
        for tried in count(0):  # for infinity
            resource = self._next()

            try:
                return self.fun(resource, **kwargs), resource
            except self.predicate:
                if tried >= len(self.resources) - 1:
                    raise

    def close(self):
        pass

    def __repr__(self):
        return "<FairCycle: %r/%r %r>" % (self.pos, len(self.resources),
                                          self.resources, )
