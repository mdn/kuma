from urlparse import parse_qs, urlparse

import pytest

from pages.admin import AdminLogin
from pages.dashboard import DashboardPage, MacroDashboardPage
from utils.decorators import (
    skip_if_maintenance_mode,
    skip_if_not_maintenance_mode,
)


@pytest.mark.smoke
@pytest.mark.nondestructive
def test_dashboard(base_url, selenium):
    page = DashboardPage(selenium, base_url).open()
    first_row = page.first_row
    # ip toggle not present
    assert not page.is_ip_toggle_present
    # ip ban not present
    assert not first_row.is_ip_ban_present
    # spam ham button not present
    assert not first_row.is_spam_ham_button_present
    # no dashboard-details
    assert page.details_items_length is 0


@pytest.mark.smoke
@pytest.mark.nondestructive
def test_dashboard_open_details(base_url, selenium):
    page = DashboardPage(selenium, base_url).open()
    # no dashboard-details
    assert page.details_items_length is 0
    # click first cell
    page.open_first_details()
    # dashboard-details exist and are visible
    assert page.details_items_length is 1
    assert page.is_first_details_displayed
    # contains a diff
    page.wait_for_first_details_diff_displayed()


@pytest.mark.smoke
@pytest.mark.nondestructive
def test_dashboard_load_page_two(base_url, selenium):
    page = DashboardPage(selenium, base_url).open()
    # save id of first revision on page one
    first_row_id = page.first_row_id
    # click on page two link
    page.click_page_two()
    # save id of first revision on page tw0
    new_first_row_id = page.first_row_id
    # check first revison on page one is not on page two
    assert first_row_id is not new_first_row_id


@pytest.mark.xfail(reason='bug 1405690: fails for some revision diffs')
@pytest.mark.smoke
@pytest.mark.nondestructive
def test_dashboard_overflow(base_url, selenium):
    """
    The revision detail diff stays in page boundaries

    bug 1405690 - some content causes overflows
    """
    page = DashboardPage(selenium, base_url).open()
    page.open_first_details()
    assert page.scroll_width <= page.client_width


@pytest.mark.nondestructive
@skip_if_not_maintenance_mode
def test_dashboard_in_mm(base_url, selenium):
    page = DashboardPage(selenium, base_url).open()
    assert page.is_maintenance_mode_banner_displayed
    assert not page.header.is_signin_displayed


@pytest.mark.smoke
@pytest.mark.login
@pytest.mark.nondestructive
@skip_if_maintenance_mode
def test_dashboard_moderator(base_url, selenium):
    admin = AdminLogin(selenium, base_url).open()
    admin.login_moderator_user()
    page = DashboardPage(selenium, base_url).open()
    first_row = page.first_row
    # ip toggle not present
    assert not page.is_ip_toggle_present
    # ip ban not present
    assert not first_row.is_ip_ban_present
    # spam ham button present
    assert first_row.is_spam_ham_button_present


@pytest.mark.smoke
@pytest.mark.login
@pytest.mark.nondestructive
@skip_if_maintenance_mode
def test_dashboard_super(base_url, selenium):
    admin = AdminLogin(selenium, base_url).open()
    admin.login_super_user()
    page = DashboardPage(selenium, base_url).open()
    first_row = page.first_row
    # ip toggle present
    assert page.is_ip_toggle_present
    # ip ban present
    assert first_row.is_ip_ban_present
    # spam ham button present
    assert first_row.is_spam_ham_button_present


@pytest.mark.nondestructive
def test_macros(base_url, selenium):
    """/en-US/dashboards/macros returns the active macros list."""
    # Open and check macros dashboard
    page = MacroDashboardPage(selenium, base_url).open()
    assert selenium.title == page.TITLE
    assert page.has_table
    first_source_link = page.first_source_link
    name = first_source_link.text
    href = first_source_link.get_attribute('href')
    assert href.startswith(
        'https://github.com/mdn/kumascript/blob/master/macros/' + name)

    # Click link to Github
    first_source_link.click()
    page.wait.until(lambda s: selenium.title != page.TITLE)
    assert selenium.current_url == href


@pytest.mark.nondestructive
def test_macros_search_en_by_click(base_url, selenium):
    """/en-US/dashboards/macros links to the English search results."""
    page = MacroDashboardPage(selenium, base_url).open()
    if not page.has_usage_counts:
        # ElasticSearch not ready, no search link to click
        return

    name = page.first_source_link.text
    page.click_first_en_search()
    page.wait.until(lambda s: selenium.title != page.TITLE)
    url_bits = urlparse(selenium.current_url)
    query = parse_qs(url_bits.query)
    assert query == {
        'locale': ['en-US'],
        'topic': ['none'],
        'kumascript_macros': [name]
    }


@pytest.mark.nondestructive
def test_macros_search_all_by_click(base_url, selenium):
    """/en-US/dashboards/macros links to complete search results."""
    page = MacroDashboardPage(selenium, base_url).open()
    if not page.has_usage_counts:
        # ElasticSearch not ready, no search link to click
        return

    name = page.first_source_link.text
    page.click_first_all_search()
    page.wait.until(lambda s: selenium.title != page.TITLE)
    url_bits = urlparse(selenium.current_url)
    query = parse_qs(url_bits.query)
    assert query == {
        'locale': ['*'],
        'topic': ['none'],
        'kumascript_macros': [name]
    }


@pytest.mark.nondestructive
def test_macros_search_en_by_form(base_url, selenium):
    """Manual search form can search all English pages."""
    if selenium.capabilities['browserName'] == 'firefox':
        pytest.xfail('"click()" on the macro form-search buttons '
                     'does not currently work for Firefox')
    page = MacroDashboardPage(selenium, base_url).open()
    page.manual_search('CSSRef', 'en-US')
    url_bits = urlparse(selenium.current_url)
    query = parse_qs(url_bits.query)
    assert query == {
        'locale': ['en-US'],
        'topic': ['none'],
        'kumascript_macros': ['CSSRef']
    }


@pytest.mark.nondestructive
def test_macros_search_all_by_form(base_url, selenium):
    """Manual search form can search all pages."""
    if selenium.capabilities['browserName'] == 'firefox':
        pytest.xfail('"click()" on the macro form-search buttons '
                     'does not currently work for Firefox')
    page = MacroDashboardPage(selenium, base_url).open()
    page.manual_search('CSSRef')
    url_bits = urlparse(selenium.current_url)
    query = parse_qs(url_bits.query)
    assert query == {
        'locale': ['*'],
        'topic': ['none'],
        'kumascript_macros': ['CSSRef']
    }
