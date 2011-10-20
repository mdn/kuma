from datetime import date

from httplib import HTTPSConnection
from urlparse import urlparse

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
    data['_ri_'] = getattr(settings, 'RESPONSYS',
        'X0Gzc2X%3DUQpglLjHJlTQTtQ1vQ2rQ0bQQzgQvQy8KVwjpnpgHlpgneHmgJoXX0G' + 
        'zc2X%3DUQpglLjHJlTQTtQ1vQ2rQ0aQQGQvQwPD')

    api_url = getattr(settings, 'RESPONSYS_API_URL',
                      'https://awesomeness.mozilla.org/pub/rf')
    if not api_url.lower().startswith('https://'):
        raise Exception('Responsys API URL must start with HTTPS.')

    u = urlparse(api_url)
    conn = HTTPSConnection(u.netloc)

    params = urlencode(data)
    headers = {"Content-type": "application/x-www-form-urlencoded",
               "Accept": "text/plain"}

    try:
        conn.request('POST', u.path, params, headers)
        response = conn.getresponse()
        return response.status == 200
    except Exception, ce:
        raise Exception('Newsletter subscription failed: %s' % ce)
