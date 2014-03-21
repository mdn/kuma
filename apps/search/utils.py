from itertools import islice
from urlobject import URLObject


class QueryURLObject(URLObject):

    def pop_query_param(self, name, value):
        """
        Removes the parameter with the given name and value -- if it exists.
        """
        params = {}
        for param, defaults in self.query.multi_dict.items():
            if param == name:
                for default in defaults:
                    if default != value:
                        params.setdefault(param, []).append(default)
            else:
                params[param] = defaults
        return self.del_query_param(name).set_query_params(params)

    def merge_query_param(self, name, value):
        """
        Adds a query parameter with the given name and value -- but prevents
        duplication.
        """
        params = self.query.multi_dict
        if name in params:
            for param, defaults in params.items():
                if param == name:
                    if value not in defaults:
                        defaults.append(value)
                params[param] = defaults
        else:
            params[name] = value
        return self.set_query_params(params)


def chunked(iterable, n):
    """Return chunks of n length of iterable.

    If ``len(iterable) % n != 0``, then the last chunk will have
    length less than n.

    Example:

    >>> chunked([1, 2, 3, 4, 5], 2)
    [(1, 2), (3, 4), (5,)]

    :arg iterable: the iterable
    :arg n: the chunk length

    :returns: generator of chunks from the iterable
    """
    iterable = iter(iterable)
    while 1:
        t = tuple(islice(iterable, n))
        if t:
            yield t
        else:
            return


def format_time(time_to_go):
    """Return minutes and seconds string for given time in seconds.

    :arg time_to_go: Number of seconds to go.

    :returns: string representation of how much time to go.
    """
    if time_to_go < 60:
        return '%ds' % time_to_go
    return '%dm %ds' % (time_to_go / 60, time_to_go % 60)
