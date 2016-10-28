import requests

# https://github.com/mozilla/bedrock/blob/master/tests/redirects/base.py
def get_abs_url(url, base_url):
    try:
        if url.pattern.startswith('/'):
            # url is a compiled regular expression pattern
            return re.compile(''.join([re.escape(base_url), url.pattern]))
    except AttributeError:
        if url.startswith('/'):
            # urljoin messes with query strings too much
            return ''.join([base_url, url])
    return url


# https://github.com/mozilla/bedrock/blob/master/tests/redirects/base.py
def url_test(url, location=None, status_code=requests.codes.moved_permanently,
             req_headers=None, req_kwargs=None, resp_headers=None, query=None,
             follow_redirects=False, final_status_code=requests.codes.ok):
    """
    Function for producing a config dict for the redirect test.

    You can use simple bash style brace expansion in the `url` and `location`
    values. If you need the `location` to change with the `url` changes you must
    use the same number of expansions or the `location` will be treated as non-expandable.

    If you use brace expansion this function will return a list of dicts instead of a dict.
    You must use the `flatten` function provided to prepare your test fixture if you do this.

    If you combine brace expansion with a compiled regular expression pattern you must
    escape any backslashes as this is the escape character for brace expansion.

    example:

        url_test('/about/drivers{/,.html}', 'https://wiki.mozilla.org/Firefox/Drivers'),
        url_test('/projects/index.{de,fr,hr,sq}.html', '/{de,fr,hr,sq}/firefox/products/'),
        url_test('/firefox/notes/', re.compile(r'\/firefox\/[\d\.]+\/releasenotes\/'),
        url_test('/firefox/android/{,beta/}notes/', re.compile(r'\\/firefox\\/android\\/[\\d\\.]+{,beta}\\/releasenotes\\/'

    :param url: The URL in question (absolute or relative).
    :param location: If a redirect, either the expected value or a compiled regular expression to match the "Location" header.
    :param status_code: Expected status code from the request.
    :param req_headers: Extra headers to send with the request.
    :param req_kwargs: Extra arguments to pass to requests.get()
    :param resp_headers: Dict of headers expected in the response.
    :param query: Dict of expected query params in `location` URL.
    :param follow_redirects: Boolean indicating whether redirects should be followed.
    :param final_status_code: Expected status code after following any redirects.
    :return: dict or list of dicts
    """
    test_data = {
        'url': url,
        'location': location,
        'status_code': status_code,
        'req_headers': req_headers,
        'req_kwargs': req_kwargs,
        'resp_headers': resp_headers,
        'query': query,
        'follow_redirects': follow_redirects,
        'final_status_code': final_status_code,
    }
    expanded_urls = list(braceexpand(url))
    num_urls = len(expanded_urls)
    if num_urls == 1:
        return test_data

    try:
        # location is a compiled regular expression pattern
        location_pattern = location.pattern
        test_data['location'] = location_pattern
    except AttributeError:
        location_pattern = None

    new_urls = []
    if location:
        expanded_locations = list(braceexpand(test_data['location']))
        num_locations = len(expanded_locations)

    for i, url in enumerate(expanded_urls):
        data = test_data.copy()
        data['url'] = url
        if location and num_urls == num_locations:
            if location_pattern is not None:
                # recompile the pattern after expansion
                data['location'] = re.compile(expanded_locations[i])
            else:
                data['location'] = expanded_locations[i]
        new_urls.append(data)

    return new_urls


def assert_valid_url(url, location=None, status_code=requests.codes.moved_permanently,
                     req_headers=None, req_kwargs=None, resp_headers=None,
                     query=None, base_url=None, follow_redirects=False,
                     final_status_code=requests.codes.ok):
    """
    Define a test of a URL's response.
    :param url: The URL in question (absolute or relative).
    :param location: If a redirect, either the expected value or a compiled regular expression to match the "Location" header.
    :param status_code: Expected status code from the request.
    :param req_headers: Extra headers to send with the request.
    :param req_kwargs: Extra arguments to pass to requests.get()
    :param resp_headers: Dict of headers expected in the response.
    :param base_url: Base URL for the site to test.
    :param query: Dict of expected query params in `location` URL.
    :param follow_redirects: Boolean indicating whether redirects should be followed.
    :param final_status_code: Expected status code after following any redirects.
    """
    kwargs = {'allow_redirects': follow_redirects}
    if req_headers:
        kwargs['headers'] = req_headers
    if req_kwargs:
        kwargs.update(req_kwargs)

    abs_url = get_abs_url(url, base_url)
    resp = requests.get(abs_url, **kwargs)
    # so that the value will appear in locals in test output
    resp_location = resp.headers.get('location')
    if follow_redirects:
        assert resp.status_code == final_status_code
    else:
        assert resp.status_code == status_code
    if location and not follow_redirects:
        if query:
            # all query values must be lists
            for k, v in query.items():
                if isinstance(v, basestring):
                    query[k] = [v]
            # parse the QS from resp location header and compare to query arg
            # since order doesn't matter.
            resp_parsed = urlparse(resp_location)
            assert query == parse_qs(resp_parsed.query)
            # strip off query for further comparison
            resp_location = resp_location.split('?')[0]

        abs_location = get_abs_url(location, base_url)
        try:
            # location is a compiled regular expression pattern
            assert abs_location.match(resp_location) is not None
        except AttributeError:
            assert abs_location == resp_location

    if resp_headers and not follow_redirects:
        for name, value in resp_headers.items():
            print name, value
            assert name in resp.headers
            assert resp.headers[name].lower() == value.lower()


# https://github.com/mozilla/bedrock/blob/master/tests/redirects/base.py
def flatten(urls_list):
    """Take a list of dicts which may itself contain some lists of dicts, and
       return a generator that will return just the dicts in sequence.

       Example:

       list(flatten([{'dude': 'jeff'}, [{'walter': 'walter'}, {'donny': 'dead'}]]))
       > [{'dude': 'jeff'}, {'walter': 'walter'}, {'donny': 'dead'}]
    """
    for url in urls_list:
        if isinstance(url, dict):
            yield url
        else:
            for sub_url in url:
                yield sub_url
