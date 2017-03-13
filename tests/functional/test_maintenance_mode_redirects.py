from urlparse import urljoin

import pytest
import requests
from pyquery import PyQuery
from selenium.webdriver.common.by import By

from pages.base import BasePage


@pytest.mark.nondestructive
@pytest.mark.maintenance_mode
@pytest.mark.parametrize("method, uri", [
    ('get', 'admin/login'),
    ('post', 'admin/login'),
    ('get', 'admin/logout'),
    ('post', 'admin/logout'),
    ('get', 'admin/password_change'),
    ('post', 'admin/password_change'),
    ('get', '{locale}/docs/User:anonymous:uitest$edit'),
    ('post', '{locale}/docs/User:anonymous:uitest$edit'),
    ('get', '{locale}/docs/User:anonymous:uitest$edit/1'),
    ('post', '{locale}/docs/User:anonymous:uitest$edit/1'),
    ('get', '{locale}/docs/User:anonymous:uitest$files'),
    ('post', '{locale}/docs/User:anonymous:uitest$files'),
    ('put', '{locale}/docs/User:anonymous:uitest$files'),
    ('get', '{locale}/docs/User:anonymous:uitest$translate'),
    ('post', '{locale}/docs/User:anonymous:uitest$translate'),
    ('get', '{locale}/docs/User:anonymous:uitest$locales'),
    ('get', '{locale}/docs/User:anonymous:uitest$move'),
    ('post', '{locale}/docs/User:anonymous:uitest$move'),
    ('post', '{locale}/docs/User:anonymous:uitest$quick-review'),
    ('get', '{locale}/docs/User:anonymous:uitest$revert/1'),
    ('post', '{locale}/docs/User:anonymous:uitest$revert/1'),
    ('get', '{locale}/docs/User:anonymous:uitest$repair_breadcrumbs'),
    ('get', '{locale}/docs/User:anonymous:uitest$delete'),
    ('post', '{locale}/docs/User:anonymous:uitest$delete'),
    ('get', '{locale}/docs/User:anonymous:uitest$restore'),
    ('get', '{locale}/docs/User:anonymous:uitest$purge'),
    ('post', '{locale}/docs/User:anonymous:uitest$purge'),
    ('post', '{locale}/docs/User:anonymous:uitest$subscribe'),
    ('post', '{locale}/docs/User:anonymous:uitest$subscribe_to_tree'),
    ('post', '{locale}/docs/preview-wiki-content'),
    ('get', '{locale}/docs/new'),
    ('post', '{locale}/docs/new'),
    ('post', '{locale}/docs/submit_akismet_spam'),
    ('get', '{locale}/dashboards/spam'),
    ('get', '{locale}/profiles/hermione/edit'),
    ('post', '{locale}/profiles/hermione/edit'),
    ('get', '{locale}/profiles/malfoy/delete'),
    ('get', '{locale}/profile'),
    ('get', '{locale}/profile/edit'),
    ('get', '{locale}/users/signin'),
    ('get', '{locale}/users/signout'),
    ('post', '{locale}/users/signout'),
    ('get', '{locale}/users/account/signup'),
    ('post', '{locale}/users/account/signup'),
    ('get', '{locale}/users/account/email'),
    ('post', '{locale}/users/account/email'),
    ('get', '{locale}/users/account/email/confirm/x'),
    ('post', '{locale}/users/account/email/confirm/x'),
    ('get', '{locale}/users/account/keys'),
    ('get', '{locale}/users/account/keys/new'),
    ('post', '{locale}/users/account/keys/new'),
    ('get', '{locale}/users/account/keys/1/history'),
    ('get', '{locale}/users/account/keys/1/delete'),
    ('post', '{locale}/users/account/keys/1/delete'),
    ('get', '{locale}/users/ban/malfoy'),
    ('post', '{locale}/users/ban/malfoy'),
    ('get', '{locale}/users/ban_user_and_cleanup/malfoy'),
    ('post', '{locale}/users/ban_user_and_cleanup_summary/malfoy'),
    ('post', '{locale}/users/account/recover/send'),
    ('get', '{locale}/users/account/recover/done'),
    ('get', '{locale}/users/account/recover/x/x-1'),
    ('get', '{locale}/users/github/login/'),
    ('get', '{locale}/users/github/login/callback/'),
    ('get', '{locale}/unsubscribe/1'),
    ('post', '{locale}/unsubscribe/1'),
])
def test_redirect(base_url, selenium, method, uri):
    HEADING_TEXT = 'Maintenance Mode'
    HEADING_SELECTOR = '#content-main > h1'
    MM_URL_TEMPLATE = '{locale}/maintenance-mode'

    locale = 'en-US'

    url = urljoin(base_url, uri.format(locale=locale))

    if method.lower() == 'get':
        # We do a get on the given URL but wait for the
        # maintenance-mode page to load via redirection.
        selenium.get(url)
        mm_page = BasePage(selenium, base_url, locale=locale)
        mm_page.URL_TEMPLATE = MM_URL_TEMPLATE
        mm_page.wait_for_page_to_load()
        mm_heading = mm_page.find_element(By.CSS_SELECTOR, HEADING_SELECTOR)
        assert mm_heading.is_displayed()
        assert HEADING_TEXT in mm_heading.text
        assert mm_page.is_maintenance_mode_banner_displayed
        assert not mm_page.header.is_signin_displayed
    else:
        request_method = getattr(requests, method.lower())
        resp = request_method(url, allow_redirects=True)
        # The final response should be a successful load of the
        # maintenance-mode page in the given locale.
        assert resp.status_code == 200
        assert resp.url == urljoin(base_url,
                                   MM_URL_TEMPLATE.format(locale=locale))
        pq = PyQuery(resp.text)
        assert HEADING_TEXT in pq(HEADING_SELECTOR).text()
        assert (BasePage.MM_BANNER_TEXT in
                pq(BasePage.MM_BANNER_SELECTOR).text())
        assert not pq.is_(BasePage.Header.SIGNIN_SELECTOR)
