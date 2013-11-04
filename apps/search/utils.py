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
