#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'Alberto Paro'
__all__ = ["get_values"]

#useful to raise ad invali import
import django

from types import NoneType
import datetime

#--- taken from http://djangosnippets.org/snippets/2278/

def get_values(instance, go_into={}, exclude=(), extra=(), skip_none=False):
    """
    Transforms a django model instance into an object that can be used for
    serialization. 
    @param instance(django.db.models.Model) - the model in question
    @param go_into(dict) - relations with other models that need expanding
    @param exclude(tuple) - fields that will be ignored
    @param extra(tuple) - additional functions/properties which are not fields
    @param skip_none(bool) - skip None field

    Usage:
    get_values(MyModel.objects.get(pk=187),
               {'user': {'go_into': ('clan',),
                         'exclude': ('crest_blob',),
                         'extra': ('get_crest_path',)}},
               ('image'))

    """
    from django.db.models.manager import Manager
    from django.db.models import Model

    SIMPLE_TYPES = (int, long, str, list, dict, tuple, bool, float, bool,
                    unicode, NoneType)

    if not isinstance(instance, Model):
        raise TypeError("Argument is not a Model")

    value = {
        'pk': instance.pk,
    }

    # check for simple string instead of tuples
    # and dicts; this is shorthand syntax
    if isinstance(go_into, str):
        go_into = {go_into: {}}

    if isinstance(exclude, str):
        exclude = (exclude,)

    if isinstance(extra, str):
        extra = (extra,)

    # process the extra properties/function/whatever
    for field in extra:
        property = getattr(instance, field)

        if callable(property):
            property = property()

        if skip_none and property is None:
            continue
        elif isinstance(property, SIMPLE_TYPES):
            value[field] = property
        else:
            value[field] = repr(property)

    field_options = instance._meta.get_all_field_names()
    for field in field_options:
        try:
            property = getattr(instance, field)
        except:
            continue
        if skip_none and property is None:
            continue

        if field in exclude or field[0] == '_' or isinstance(property, Manager):
            # if it's in the exclude tuple, ignore it 
            # if it's a "private" field, ignore it 
            # if it's an instance of manager (this means a more complicated
            # relationship), ignore it 
            continue
        elif go_into.has_key(field):
            # if it's in the go_into dict, make a recursive call for that field
            try:
                field_go_into = go_into[field].get('go_into', {})
            except AttributeError:
                field_go_into = {}

            try:
                field_exclude = go_into[field].get('exclude', ())
            except AttributeError:
                field_exclude = ()

            try:
                field_extra = go_into[field].get('extra', ())
            except AttributeError:
                field_extra = ()

            value[field] = get_values(property,
                                      field_go_into,
                                      field_exclude,
                                      field_extra, skip_none=skip_none)
        else:
            if isinstance(property, Model):
                # if it's a model, we need it's PK #
                value[field] = property.pk
            elif isinstance(property, (datetime.date,
                                       datetime.time,
                                       datetime.datetime)):
                value[field] = property
            else:
                # else, we just put the value #
                if callable(property):
                    property = property()

                if isinstance(property, SIMPLE_TYPES):
                    value[field] = property
                else:
                    value[field] = repr(property)

    return value
