# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from django.http import HttpResponseRedirect

from django.utils.http import urlencode

import commonware

log = commonware.log.getLogger('kuma.dekicompat')

def logout(request):
    """ Clear Django user from session and let Dekiwiki do it's thang...
        returntotitle is a Deki idiom, do not change!
    """
    request.session.flush()
    rtt = request.GET.get('returntotitle', "/")
    params = {'title': "Special:Userlogout",
              'returntotitle': rtt}
    return HttpResponseRedirect("index.php?%s" % urlencode(params))
