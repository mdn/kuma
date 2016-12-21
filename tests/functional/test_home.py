import pytest

from pages.home import HomePage


# homepage tests
@pytest.mark.smoke
@pytest.mark.nodata
@pytest.mark.nondestructive
def test_masthead_displayed(base_url, selenium):
    page = HomePage(selenium, base_url).open()
    assert page.is_masthead_displayed


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


@pytest.mark.smoke
@pytest.mark.nodata
@pytest.mark.nondestructive
def test_header_signin(base_url, selenium):
    page = HomePage(selenium, base_url).open()
    # click on sign in widget
    page.header.trigger_signin()
    # assert it's fowarded to github
    assert 'https://github.com' in str(selenium.current_url)


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
