"""Tests for scraping live data and creating sample data."""


from unittest import mock


def mock_requester(
        requester_spec=None, response_spec=None, content=None, json=None,
        status_code=200, history=None, final_path=None):
    """
    Create mock production data requester for Source.gather testing.

    Keyword Arguments:
    requester_spec - Requester attributes (default request)
    response_spec - Response attributes (default content, history)
    content - Content of response (default "")
    json - Decoded JSON of response (default not JSON)
    status_code - Status code of response (default 200, None to error on check)
    history - (status_code, path) pairs for redirect history of request
        (default no redirects)
    final_path - Final path for request (default None)
    """
    if requester_spec is None:
        requester_spec = ['request']
    if response_spec is None:
        response_spec = ['content', 'history', 'status_code']

    requester = mock.Mock(spec_set=requester_spec)
    if 'request' in requester_spec:
        mock_response = mock.Mock(spec_set=response_spec)
        if 'content' in response_spec:
            mock_response.content = content or ""
        if 'history' in response_spec:
            redirect_history = []
            for status_code, path in (history or []):
                redirect_response = mock.Mock(spec_set=['status_code', 'url'])
                redirect_response.status_code = status_code
                redirect_response.url = path
                redirect_history.append(redirect_response)
            mock_response.history = redirect_history
        if 'json' in response_spec and json:
            mock_response.json.return_value = json
        if 'status_code' in response_spec and status_code:
            mock_response.status_code = status_code
        if 'url' in response_spec:
            assert final_path, "Need a final_path for response.url"
            mock_response.url = final_path
        requester.request.return_value = mock_response
    return requester


def mock_storage(spec=None):
    """
    Create mock database storage for Source.gather testing.

    Keyword Arguments:
    spec - List of expected Storage method calls (default [])

    Any spec that starts with "get_" is initialized to return None.
    """
    spec_set = spec or []
    storage = mock.Mock(spec_set=spec_set)
    for item in spec_set:
        if item.startswith('get_'):
            getattr(storage, item).return_value = None
    return storage
