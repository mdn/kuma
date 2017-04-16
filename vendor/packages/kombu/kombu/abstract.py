"""
kombu.compression
=================

Object utilities.

:copyright: (c) 2009 - 2012 by Ask Solem.
:license: BSD, see LICENSE for more details.

"""
from __future__ import absolute_import

from copy import copy

from .exceptions import NotBoundError

__all__ = ["Object", "MaybeChannelBound"]


def unpickle_dict(cls, kwargs):
    return cls(**kwargs)


class Object(object):
    """Common base class supporting automatic kwargs->attributes handling,
    and cloning."""
    attrs = ()

    def __init__(self, *args, **kwargs):
        any = lambda v: v
        for name, type_ in self.attrs:
            value = kwargs.get(name)
            if value is not None:
                setattr(self, name, (type_ or any)(value))
            else:
                try:
                    getattr(self, name)
                except AttributeError:
                    setattr(self, name, None)

    def setdefault(self, **defaults):
        for key, value in defaults.iteritems():
            if getattr(self, key) is None:
                setattr(self, key, value)

    def as_dict(self, recurse=False):
        def f(obj):
            if recurse and isinstance(obj, Object):
                return obj.as_dict(recurse=True)
            return obj
        return dict((attr, f(getattr(self, attr))) for attr, _ in self.attrs)

    def __reduce__(self):
        return unpickle_dict, (self.__class__, self.as_dict())

    def __copy__(self):
        return self.__class__(**self.as_dict())


class MaybeChannelBound(Object):
    """Mixin for classes that can be bound to an AMQP channel."""
    _channel = None
    _is_bound = False

    #: Defines whether maybe_declare can skip declaring this entity twice.
    can_cache_declaration = False

    def __call__(self, channel):
        """`self(channel) -> self.bind(channel)`"""
        return self.bind(channel)

    def bind(self, channel):
        """Create copy of the instance that is bound to a channel."""
        return copy(self).maybe_bind(channel)

    def maybe_bind(self, channel):
        """Bind instance to channel if not already bound."""
        if not self.is_bound and channel:
            self._channel = channel
            self.when_bound()
            self._is_bound = True
        return self

    def revive(self, channel):
        """Revive channel after the connection has been re-established.

        Used by :meth:`~kombu.connection.BrokerConnection.ensure`.

        """
        if self.is_bound:
            self._channel = channel
            self.when_bound()

    def when_bound(self):
        """Callback called when the class is bound."""
        pass

    def __repr__(self, item=""):
        if self.is_bound:
            return "<bound %s of %s>" % (item or self.__class__.__name__,
                                         self.channel)
        return "<unbound %s>" % (item, )

    @property
    def is_bound(self):
        """Flag set if the channel is bound."""
        return self._is_bound and self._channel is not None

    @property
    def channel(self):
        """Current channel if the object is bound."""
        if self._channel is None:
            raise NotBoundError(
                "Can't call method on %s not bound to a channel" % (
                    self.__class__.__name__))
        return self._channel
