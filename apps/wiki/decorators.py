# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from waffle import flag_is_active

from wiki import ReadOnlyException


def check_readonly(view):
    def _check_readonly(request, *args, **kwargs):
        if not flag_is_active(request, 'kumaediting'):
            raise ReadOnlyException("kumaediting")
        elif flag_is_active(request, 'kumabanned'):
            raise ReadOnlyException("kumabanned")

        return view(request, *args, **kwargs)
    return _check_readonly
