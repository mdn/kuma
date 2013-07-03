# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from zlib import crc32


class peekable(object):
    """Wrapper for an iterator to allow 1-item lookahead"""
    # Lowercase to blend in with itertools. The fact that it's a class is an
    # implementation detail.

    # TODO: Liberate into itertools.

    def __init__(self, iterable):
        self._it = iter(iterable)

    def __iter__(self):
        return self

    def __nonzero__(self):
        try:
            self.peek()
        except StopIteration:
            return False
        return True

    def peek(self):
        """Return the item that will be next returned from next().

        Raise StopIteration if there are no items left.

        """
        if not hasattr(self, '_peek'):
            self._peek = self._it.next()
        return self._peek

    def next(self):
        ret = self.peek()
        del self._peek
        return ret


def merge(*iterables, **kwargs):
    """Return an iterable ordered merge of the already-sorted items
    from each of `iterables`, compared by kwarg `key`.

    If reverse=True is passed, iterables must return their results in
    descending order rather than ascending.

    """
    # TODO: Liberate into the stdlib.
    key = kwargs.pop('key', lambda a: a)
    reverse = kwargs.pop('reverse', False)

    min_or_max = max if reverse else min
    peekables = [peekable(it) for it in iterables]
    peekables = [p for p in peekables if p]  # Kill empties.
    while peekables:
        _, p = min_or_max((key(p.peek()), p) for p in peekables)
        yield p.next()
        peekables = [p for p in peekables if p]


def hash_to_unsigned(data):
    """If data is a string or unicode string, return an unsigned 4-byte int
    hash of it. If data is already an int that fits those parameters, return it
    verbatim.

    If data is an int outside that range, behavior is undefined at the moment.
    We rely on the PositiveIntegerField on WatchFilter to scream if the int is
    too long for the field.

    """
    if isinstance(data, basestring):
        # Return a CRC32 value identical across Python versions and platforms
        # by stripping the sign bit as on
        # http://docs.python.org/library/zlib.html. Though CRC32 is not a good
        # general-purpose hash function, it has no collisions on a dictionary
        # of 38,470 English words, which should be fine for the small sets that
        # watch filters are designed to enumerate. As a bonus, it is fast and
        # available as a built-in function in some DBs. If your set of filter
        # values is very large or has different CRC32 distribution properties
        # than English words, you might want to do your own hashing in your
        # Event subclass and pass ints when specifying filter values.
        return crc32(data.encode('utf-8')) & 0xffffffff
    else:
        return int(data)
