#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2014 Zuza Software Foundation
#
# This file is part of translate.
#
# translate is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation; either version 2 of the License, or (at your option) any later
# version.
#
# translate is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with
# this program; if not, see <http://www.gnu.org/licenses/>.

import warnings
from functools import wraps


def deprecated(message=""):
    """Decorator that marks functions and methods as deprecated.

    A warning will be emitted when the function or method is used. If a custom
    message is provided, it will be shown after the default warning message.
    """
    def inner_render(func):
        @wraps(func)
        def new_func(*args, **kwargs):
            msg = message  # Hack to avoid UnboundLocalError.
            if msg:
                msg = "\n" + msg
            warnings.warn_explicit(
                "Call to deprecated function {0}.{1}".format(func.__name__,
                                                             msg),
                category=DeprecationWarning,
                filename=func.func_code.co_filename,
                lineno=func.func_code.co_firstlineno + 1
            )
            return func(*args, **kwargs)
        return new_func
    return inner_render
