import logging

from django.utils.translation import gettext_lazy as _
from urlobject import URLObject


log = logging.getLogger("kuma.search.utils")


SEARCH_DOWN_DETAIL = _(
    "Search is temporarily unavailable. " "Please try again in a few minutes."
)

SEARCH_ERROR_DETAIL = _(
    "Something went wrong with the search query. " "Please try again in a few minutes."
)


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
        return self.del_query_param(name).set_query_params(self.clean_params(params))

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
            if isinstance(default, (list, tuple)):
                # set all items with an empty value to an empty string
                default = [item or "" for item in default]
                if len(default) == 1:
                    default = default[0]
            if isinstance(default, str):
                default = default.strip()
            # make sure the parameter name and value aren't empty
            if param and default:
                clean_params[param] = default
        return clean_params
