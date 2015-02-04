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
        return (self.del_query_param(name)
                    .set_query_params(self.clean_params(params)))

    def merge_query_param(self, name, value):
        """
        Adds a query parameter with the given name and value -- but prevents
        duplication.
        """
        params = self.query.multi_dict
        if name in params:
            for param, defaults in params.items():
                if param == name:
                    if value not in defaults and value not in (None, [None]):
                        defaults.append(value)
        else:
            params[name] = value
        return self.without_query().set_query_params(self.clean_params(params))

    def clean_params(self, params):
        """
        Cleans query parameters that don't have a value to not freak out
        urllib's quoting and Django's form system.
        """
        clean_params = {}
        for param, default in params.items():
            if isinstance(default, list) and len(default) == 1:
                default = default[0]
            if isinstance(default, basestring):
                default = default.strip()
            if default not in ('', None):
                clean_params[param] = default
        return clean_params


def format_time(time_to_go):
    """Return minutes and seconds string for given time in seconds.

    :arg time_to_go: Number of seconds to go.

    :returns: string representation of how much time to go.
    """
    if time_to_go < 60:
        return '%ds' % time_to_go
    return '%dm %ds' % (time_to_go / 60, time_to_go % 60)
