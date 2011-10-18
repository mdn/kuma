from datetime import date

import pycurl

from django.conf import settings
from django.utils.http import urlencode


def make_source_url(request):
    return request.get_host() + request.get_full_path()


def subscribe(campaign, address, format='html', source_url='', lang='', country=''):
    """
    Subscribe a user to a list in responsys. There should be two
    fields within the Responsys system named by the "campaign"
    parameter: <campaign>_FLG and <campaign>_DATE
    """
    data = {
        'LANG_LOCALE': lang,
        'COUNTRY_': country,
        'SOURCE_URL': source_url,
        'EMAIL_ADDRESS_': address,
        'EMAIL_FORMAT_': 'H' if format == 'html' else 'T',
        }

    data['%s_FLG' % campaign] = 'Y'
    data['%s_DATE' % campaign] = date.today().strftime('%Y-%m-%d')

    # views.py asserts setting is available
    data['_ri_'] = settings.RESPONSYS

    if not settings.RESPONSYS_API_URL.lower().startswith('https://'):
        raise Exception('Responsys API URL must start with HTTPS.')

    curl = pycurl.Curl()
    # Ensure SSL cert validates before sending user data over the wire
    curl.setopt(pycurl.SSL_VERIFYPEER, 1)
    curl.setopt(pycurl.SSL_VERIFYHOST, 2)
    curl.setopt(pycurl.URL, settings.RESPONSYS_API_URL)
    # Add POST data
    curl.setopt(pycurl.POST, 1)
    curl.setopt(pycurl.POSTFIELDS, urlencode(data))
    try:
        curl.perform()
    except Exception, ce:
        raise Exception('Newsletter subscription failed: %s' % ce)
    else:
        return curl.getinfo(pycurl.RESPONSE_CODE) == 200

