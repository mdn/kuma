"""
kombu.utils.debug
=================

Debugging support.

:copyright: (c) 2009 - 2012 by Ask Solem.
:license: BSD, see LICENSE for more details.

"""
from __future__ import absolute_import

import logging

from functools import wraps

from kombu.log import get_logger

__all__ = ["setup_logging", "Logwrapped"]


def setup_logging(loglevel=logging.DEBUG, loggers=["kombu.connection",
                                                   "kombu.channel"]):
    for logger in loggers:
        l = get_logger(logger)
        l.addHandler(logging.StreamHandler())
        l.setLevel(loglevel)


class Logwrapped(object):
    __ignore = ("__enter__", "__exit__")

    def __init__(self, instance, logger=None, ident=None):
        self.instance = instance
        self.logger = get_logger(logger)
        self.ident = ident

    def __getattr__(self, key):
        meth = getattr(self.instance, key)

        if not callable(meth) or key in self.__ignore:
            return meth

        @wraps(meth)
        def __wrapped(*args, **kwargs):
            info = ""
            if self.ident:
                info += self.ident % vars(self.instance)
            info += "%s(" % (meth.__name__, )
            if args:
                info += ", ".join(map(repr, args))
            if kwargs:
                if args:
                    info += ", "
                info += ", ".join("%s=%r" % (key, value)
                                    for key, value in kwargs.iteritems())
            info += ")"
            self.logger.debug(info)
            return meth(*args, **kwargs)

        return __wrapped

    def __repr__(self):
        return repr(self.instance)

    def __dir__(self):
        return dir(self.instance)
