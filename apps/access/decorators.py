from functools import wraps
import inspect

from django.db.models import Model, get_model
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404

import access


def has_perm_or_owns_or_403(perm, field_name, lookup_obj, lookup_perm_obj,
                            **kwargs):
    """Behave like has_perm_or_403 but also grant permission to owners.

    Arguments:
        field_name: Attr of model object that references the owner

        lookup_obj: Triple that specifies a lookup to the object on which
            ownership should be compared. Items in the tuple are...
            (model class or import path thereof,
             kwarg name specifying field and comparator (e.g. 'id__exact'),
             name of kwarg containing the value to which to compare)

        lookup_perm_obj: Triple that specifies a lookup to the object on which
            to check for permission. Elements of the tuple are as in
            lookup_obj.

    """
    def decorator(view_func):
        def _wrapped_view(request, *args, **kwargs):
            # from authority/decorators.py
            if request.user.is_authenticated():
                params = []
                lookup_variables = (lookup_obj, lookup_perm_obj)
                for lookup_variable in lookup_variables:
                    model, lookup, varname = lookup_variable
                    value = kwargs.get(varname, None)
                    if value is None:
                        raise ValueError("Expected kwarg '%s' not found." %
                                         varname)
                    if isinstance(model, basestring):
                        model_class = get_model(*model.split("."))
                    else:
                        model_class = model
                    if model_class is None:
                        raise ValueError(
                            "The given argument '%s' is not a valid model." %
                            model)
                    if (inspect.isclass(model_class) and
                            not issubclass(model_class, Model)):
                        raise ValueError(
                            'The argument %s needs to be a model.' % model)
                    obj = get_object_or_404(model_class, **{lookup: value})
                    params.append(obj)
                granted = access.has_perm_or_owns(request.user, perm,
                                                  params[0], params[1],
                                                  field_name)
                if granted or request.user.has_perm(perm):
                    return view_func(request, *args, **kwargs)

            # in all other cases, permission denied
            return HttpResponseForbidden()

        return wraps(view_func)(_wrapped_view)

    return decorator
