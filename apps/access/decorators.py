from functools import wraps
import inspect

from django.db.models import Model, get_model
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404

import access


def has_perm_or_owns_or_403(perm, owner_attr, obj_lookup, perm_obj_lookup,
                            **kwargs):
    """Act like permission_required_or_403 but also grant permission to owners.

    Arguments:
        owner_attr: Attr of model object that references the owner

        obj_lookup: Triple that specifies a lookup to the object on which
            ownership should be compared. Items in the tuple are...
            (model class or import path thereof,
             kwarg name specifying field and comparator (e.g. 'id__exact'),
             name of kwarg containing the value to which to compare)

        perm_obj_lookup: Triple that specifies a lookup to the object on which
            to check for permission. Elements of the tuple are as in
            obj_lookup.

    """
    def decorator(view_func):
        def _wrapped_view(request, *args, **kwargs):
            # based on authority/decorators.py
            user = request.user
            if user.is_authenticated():
                obj = _resolve_lookup(obj_lookup, kwargs)
                perm_obj = _resolve_lookup(perm_obj_lookup, kwargs)
                granted = access.has_perm_or_owns(user, perm, obj, perm_obj,
                                                  owner_attr)
                if granted or user.has_perm(perm):
                    return view_func(request, *args, **kwargs)

            # in all other cases, permission denied
            return HttpResponseForbidden()

        return wraps(view_func)(_wrapped_view)

    return decorator


def _resolve_lookup((model, lookup, arg_name), view_kwargs):
    """Return the object indicated by the lookup triple and the kwargs passed
    to the view.

    """
    value = view_kwargs.get(arg_name)
    if value is None:
        raise ValueError("Expected kwarg '%s' not found." % arg_name)
    if isinstance(model, basestring):
        model_class = get_model(*model.split('.'))
    else:
        model_class = model
    if model_class is None:
        raise ValueError("The given argument '%s' is not a valid model." %
                         model)
    if inspect.isclass(model_class) and not issubclass(model_class, Model):
        raise ValueError("The argument '%s' needs to be a model." % model)
    return get_object_or_404(model_class, **{lookup: value})
