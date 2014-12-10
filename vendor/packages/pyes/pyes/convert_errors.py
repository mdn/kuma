#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Routines for converting error responses to appropriate exceptions.

"""

__author__ = 'Richard Boulton'

__all__ = ['raise_if_error']

import pyes.exceptions

# Patterns used to map exception strings to classes.

# First, exceptions for which the messages start with the error name,
# and then contain the error description wrapped in [].
exceptions_by_name = dict((name, getattr(pyes.exceptions, name))
    for name in (
        'ElasticSearchIllegalArgumentException',
        'IndexAlreadyExistsException',
        'IndexMissingException',
        'SearchPhaseExecutionException',
        'ReplicationShardOperationFailedException',
        'ClusterBlockException',
        'MapperParsingException',
    )
)

# Second, patterns for exceptions where the message is just the error
# description, and doesn't contain an error name.  These patterns are matched
# at the end of the exception.
exception_patterns_trailing = {
    '] missing': pyes.exceptions.NotFoundException,
    '] Already exists': pyes.exceptions.AlreadyExistsException,
}

def raise_if_error(status, result):
    """Raise an appropriate exception if the result is an error.

    Any result with a status code of 400 or higher is considered an error.

    The exception raised will either be an ElasticSearchException, or a more
    specific subclass of ElasticSearchException if the type is recognised.

    The status code and result can be retrieved from the exception by accessing its
    status and result properties.

    """
    assert isinstance(status, int)

    if status < 400:
        return

    if status == 404 and isinstance(result, dict) and result.get('ok'):
        raise pyes.exceptions.NotFoundException("Item not found", status, result)

    if not isinstance(result, dict) or 'error' not in result:
        raise pyes.exceptions.ElasticSearchException("Unknown exception type", status, result)

    error = result['error']
    bits = error.split('[', 1)
    if len(bits) == 2:
        excClass = exceptions_by_name.get(bits[0], None)
        if excClass is not None:
            msg = bits[1]
            if msg.endswith(']'):
                msg = msg[:-1]
            raise excClass(msg, status, result)

    for pattern, excClass in exception_patterns_trailing.iteritems():
        if not error.endswith(pattern):
            continue
        # For these exceptions, the returned value is the whole descriptive
        # message.
        raise excClass(error, status, result)

    raise pyes.exceptions.ElasticSearchException(error, status, result)
