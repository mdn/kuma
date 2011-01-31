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
