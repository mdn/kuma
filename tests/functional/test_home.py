import pytest

from utils.urls import assert_valid_url
from pages.home import HomePage


# homepage tests
@pytest.mark.smoke
@pytest.mark.nodata
@pytest.mark.nondestructive
def test_masthead_displayed(base_url, selenium):
    page = HomePage(selenium, base_url).open()
    assert page.is_masthead_displayed


@pytest.mark.smoke
@pytest.mark.nondestructive
def test_hacks_blog(base_url, selenium):
    page = HomePage(selenium, base_url).open()
    assert page.hacks_items_length == 5
    assert_valid_url(page.hacks_url, follow_redirects=True)


@pytest.mark.smoke
@pytest.mark.nodata
@pytest.mark.nondestructive
def test_callouts(base_url, selenium):
    page = HomePage(selenium, base_url).open()
    # three of them?
    assert page.callout_items_length == 3
    # in a row
    callout_container = page.callout_container
    assert callout_container.is_expected_stacking()
    # valid links?
    callout_links = page.callout_link_list
    for link in callout_links:
        this_link = link.get_attribute('href')
        assert_valid_url(this_link, follow_redirects=True)
# header tests
@pytest.mark.smoke
@pytest.mark.nodata
@pytest.mark.nondestructive
def test_header_displays(base_url, selenium):
    page = HomePage(selenium, base_url).open()
    assert page.Header.is_displayed
    assert page.Header.is_menu_displayed


@pytest.mark.smoke
@pytest.mark.nodata
@pytest.mark.nondestructive
def test_header_platform_submenu(base_url, selenium):
    page = HomePage(selenium, base_url).open()
    assert page.header.is_platform_submenu_trigger_displayed
    assert not page.header.is_platform_submenu_displayed
    page.header.show_platform_submenu()
    assert page.header.is_platform_submenu_displayed


# footer tests
@pytest.mark.smoke
@pytest.mark.nodata
@pytest.mark.nondestructive
def test_footer_displays(base_url, selenium):
    page = HomePage(selenium, base_url).open()
    assert page.Footer.is_displayed
    assert page.Footer.is_privacy_displayed
    assert page.Footer.is_license_displayed
    assert page.Footer.is_select_language_displayed
