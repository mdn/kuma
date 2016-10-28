import pytest

from pages.home import HomePage


# homepage tests
@pytest.mark.smoke
@pytest.mark.nondestructive
def test_is_masthead_displayed(base_url, selenium):
    page = HomePage(selenium, base_url).open()
    assert page.is_masthead_displayed


# header tests
@pytest.mark.smoke
@pytest.mark.nondestructive
def test_is_header_displayed(base_url, selenium):
    page = HomePage(selenium, base_url).open()
    assert page.Header.is_displayed


@pytest.mark.smoke
@pytest.mark.nondestructive
def test_is_header_menu_displayed(base_url, selenium):
    page = HomePage(selenium, base_url).open()
    assert page.Header.is_menu_displayed


@pytest.mark.smoke
@pytest.mark.nondestructive
def test_header_platform_submenu(base_url, selenium):
    page = HomePage(selenium, base_url).open()
    assert page.header.is_platform_submenu_trigger_displayed
    assert not page.header.is_platform_submenu_displayed
    page.header.show_platform_submenu()
    assert page.header.is_platform_submenu_displayed


@pytest.mark.smoke
@pytest.mark.nondestructive
def test_header_feedback_submenu(base_url, selenium):
    page = HomePage(selenium, base_url).open()
    assert page.header.is_feedback_submenu_trigger_displayed
    assert not page.header.is_feedback_submenu_displayed
    page.header.show_feedback_submenu()
    assert page.header.is_feedback_submenu_displayed


# footer tests
@pytest.mark.smoke
@pytest.mark.nondestructive
def test_is_footer_displayed(base_url, selenium):
    page = HomePage(selenium, base_url).open()
    assert page.Footer.is_displayed


@pytest.mark.smoke
@pytest.mark.nondestructive
def test_is_footer_links_displayed(base_url, selenium):
    page = HomePage(selenium, base_url).open()
    assert page.Footer.is_privacy_displayed
    assert page.Footer.is_license_displayed


@pytest.mark.smoke
@pytest.mark.nondestructive
def test_select_language(base_url, selenium):
    page = HomePage(selenium, base_url).open()
    assert page.Footer.is_select_language_displayed
