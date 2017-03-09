import pytest

from pages.article import ArticlePage

ARTICLE_NAME = 'User:anonymous:uitest'
ARTICLE_TITLE_SUFIX = " | MDN"


@pytest.mark.smoke
@pytest.mark.nondestructive
@pytest.mark.maintenance_mode
def test_title(base_url, selenium):
    page = ArticlePage(selenium, base_url).open()
    assert (ARTICLE_NAME + ARTICLE_TITLE_SUFIX) == selenium.title
    assert page.article_title_text == ARTICLE_NAME
    assert page.article_title_text in selenium.title


# layout
@pytest.mark.smoke
@pytest.mark.nondestructive
@pytest.mark.maintenance_mode
def test_article_layout(base_url, selenium):
    page = ArticlePage(selenium, base_url).open()
    assert page.is_article_displayed
    assert page.is_article_column_left_present
    assert page.is_article_column_content_present
    assert page.article_column_right_present
    column_container = page.article_column_container_region
    assert column_container.is_expected_stacking


# page buttons
@pytest.mark.smoke
@pytest.mark.nondestructive
def test_page_buttons_displayed(base_url, selenium):
    page = ArticlePage(selenium, base_url).open()
    assert page.is_language_menu_displayed
    assert page.is_edit_button_displayed
    assert page.is_advanced_menu_displayed


# page buttons in maintenance mode
@pytest.mark.nondestructive
@pytest.mark.maintenance_mode
def test_page_buttons_displayed_in_mm(base_url, selenium):
    page = ArticlePage(selenium, base_url).open()
    assert page.is_language_menu_displayed
    assert not page.is_edit_button_displayed
    assert not page.header.is_signin_displayed
    assert not page.is_add_translation_link_available
    assert page.is_maintenance_mode_banner_displayed
    assert page.is_advanced_menu_displayed


# header tests
@pytest.mark.smoke
@pytest.mark.nondestructive
@pytest.mark.maintenance_mode
def test_header_displays(base_url, selenium):
    page = ArticlePage(selenium, base_url).open()
    assert page.header.is_displayed


@pytest.mark.smoke
@pytest.mark.nodata
@pytest.mark.nondestructive
def test_header_signin(base_url, selenium):
    page = ArticlePage(selenium, base_url).open()
    # click on sign in widget
    page.header.trigger_signin()
    # assert it's fowarded to github
    assert 'https://github.com' in str(selenium.current_url)


@pytest.mark.smoke
@pytest.mark.nondestructive
@pytest.mark.maintenance_mode
def test_header_platform_submenu(base_url, selenium):
    page = ArticlePage(selenium, base_url).open()
    assert page.header.is_platform_submenu_trigger_displayed
    assert not page.header.is_platform_submenu_displayed
    page.header.show_platform_submenu()
    assert page.header.is_platform_submenu_displayed


@pytest.mark.smoke
@pytest.mark.nondestructive
@pytest.mark.maintenance_mode
def test_header_feedback_submenu(base_url, selenium):
    page = ArticlePage(selenium, base_url).open()
    assert page.header.is_feedback_submenu_trigger_displayed
    assert not page.header.is_feedback_submenu_displayed
    page.header.show_feedback_submenu()
    assert page.header.is_feedback_submenu_displayed


# footer tests
@pytest.mark.smoke
@pytest.mark.nondestructive
@pytest.mark.maintenance_mode
def test_footer_displays(base_url, selenium):
    page = ArticlePage(selenium, base_url).open()
    assert page.footer.is_displayed
    assert page.footer.is_privacy_displayed
    assert page.footer.is_license_displayed
    assert page.footer.is_select_language_displayed
