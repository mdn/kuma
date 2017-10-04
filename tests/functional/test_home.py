import pytest

from pages.home import HomePage
from utils.urls import assert_valid_url
from utils.decorators import (
    skip_if_maintenance_mode,
    skip_if_not_maintenance_mode,
)


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
    # two of them?
    assert page.callout_items_length == 2
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
    assert page.header.is_displayed


@pytest.mark.smoke
@pytest.mark.nodata
@pytest.mark.nondestructive
def test_header_tech_submenu(base_url, selenium):
    page = HomePage(selenium, base_url).open()
    assert page.header.is_tech_submenu_trigger_displayed
    assert not page.header.is_tech_submenu_displayed
    page.header.show_tech_submenu()
    assert page.header.is_tech_submenu_displayed


@pytest.mark.smoke
@pytest.mark.nodata
@pytest.mark.nondestructive
@skip_if_maintenance_mode
def test_header_signin(base_url, selenium):
    page = HomePage(selenium, base_url).open()
    old_url = selenium.current_url
    # click on sign in widget
    page.header.trigger_signin()
    # assert it's fowarded to github
    page.wait.until(lambda s: s.current_url != old_url)
    assert 'https://github.com' in str(selenium.current_url)


@pytest.mark.nondestructive
@skip_if_not_maintenance_mode
def test_header_no_signin(base_url, selenium):
    page = HomePage(selenium, base_url).open()
    assert page.is_maintenance_mode_banner_displayed
    assert not page.header.is_signin_displayed


# footer tests
@pytest.mark.smoke
@pytest.mark.nodata
@pytest.mark.nondestructive
def test_footer_displays(base_url, selenium):
    page = HomePage(selenium, base_url).open()
    assert page.footer.is_displayed
    assert page.footer.is_privacy_displayed
    assert page.footer.is_license_displayed
    assert page.footer.is_select_language_displayed
