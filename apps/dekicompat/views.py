import logging

from django.http import HttpResponseRedirect

from django.utils.http import urlencode

log = logging.getLogger('mdn')

def logout(request):
    """ Clear Django user from session and let Dekiwiki do it's thang...
        returntotitle is a Deki idiom, do not change!
    """
    request.session.flush()
    rtt = request.GET.get('returntotitle', "/")
    params = {'title': "Special:Userlogout",
              'returntotitle': rtt}
    return HttpResponseRedirect("index.php?%s" % urlencode(params))
