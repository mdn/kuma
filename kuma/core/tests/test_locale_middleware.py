import pytest
from django.conf import settings

from . import assert_shared_cache_header
from .test_urlresolvers import WEIGHTED_ACCEPT_CASES


# Simple Accept-Language headers, one term
SIMPLE_ACCEPT_CASES = (
    ('', 'en-US'),          # No preference gets default en-US
    ('en', 'en-US'),        # Default en is en-US
    ('en-US', 'en-US'),     # Exact match for default
    ('en-us', 'en-US'),     # Case-insensitive match for default
    ('fr-FR', 'fr'),        # Overly-specified locale gets default
    ('fr-fr', 'fr'),        # Overly-specified match is case-insensitive
)
PICKER_CASES = SIMPLE_ACCEPT_CASES + WEIGHTED_ACCEPT_CASES + (
    ('xx', 'en-US'),        # Unknown in Accept-Language gets default
)
REDIRECT_CASES = [case for case in SIMPLE_ACCEPT_CASES if case[0] != case[1]]


@pytest.mark.parametrize('accept_language,locale', PICKER_CASES)
def test_locale_middleware_picker(accept_language, locale, client, db):
    '''The LocaleMiddleware picks locale from the Accept-Language header.'''
    response = client.get('/', HTTP_ACCEPT_LANGUAGE=accept_language)
    assert response.status_code == 302
    assert response['Location'] == 'http://testserver/%s/' % locale or 'en_US'
    assert_shared_cache_header(response)


@pytest.mark.parametrize('original,fixed', REDIRECT_CASES)
def test_locale_middleware_fixer(original, fixed, client, db):
    '''The LocaleMiddleware redirects for non-standard locale URLs.'''
    response = client.get('/%s/' % original)
    assert response.status_code == 302
    assert response['Location'] == 'http://testserver/%s/' % fixed
    assert_shared_cache_header(response)


def test_locale_middleware_fixer_confusion(client, db):
    '''The LocaleMiddleware treats unknown locales and 404 en-US docs.'''
    response = client.get('/xx/')
    assert response.status_code == 302
    assert response['Location'] == 'http://testserver/en-US/xx/'
    assert_shared_cache_header(response)


def test_locale_middleware_language_cookie(client, db):
    '''The LocaleMiddleware uses the language cookie.'''
    client.cookies.load({settings.LANGUAGE_COOKIE_NAME: 'bn-BD'})
    response = client.get('/')
    assert response.status_code == 302
    assert response['Location'] == 'http://testserver/bn-BD/'
    assert_shared_cache_header(response)


def test_locale_middleware_lang_query_param(client):
    '''The LocaleMiddleware redirects on the ?lang query first.'''
    client.cookies.load({settings.LANGUAGE_COOKIE_NAME: 'bn-BD'})
    response = client.get('/?lang=fr',
                          HTTP_ACCEPT_LANGUAGE='en;q=0.9, fr;q=0.8')
    assert response.status_code == 302
    assert response['Location'] == 'http://testserver/fr/'
    assert_shared_cache_header(response)
