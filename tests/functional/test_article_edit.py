import pytest

from pages.article import ArticlePage
from pages.admin import AdminLogin
from utils.decorators import skip_if_maintenance_mode


@pytest.mark.smoke
@pytest.mark.nondestructive
@skip_if_maintenance_mode
def test_edit_sign_in(base_url, selenium):
    page = ArticlePage(selenium, base_url).open()
    # click edit
    page.click_edit(False)
    # check prompted for sign in
    assert 'users/signin' in selenium.current_url


@pytest.mark.smoke
@pytest.mark.login
@pytest.mark.nondestructive
@skip_if_maintenance_mode
def test_edit(base_url, selenium):
    admin = AdminLogin(selenium, base_url).open()
    admin.login_new_user()
    article_page = ArticlePage(selenium, base_url).open()
    page = article_page.click_edit(True)
    # welcome message displays
    assert page.is_first_contrib_welcome_displayed
    # CKEditor loads and is ready
    editor = page.editor()
    assert editor.ready
    # Tagit loads
    assert page.tagit_loaded
    # save button disabled
    assert page.is_save_button_disabled
    # edit in source mode, including an iframe, exit source mode
    editor.edit_source()
    content = editor.content_source()
    # iframe edit removed
    assert 'iframe' not in content
    # content edit remains
    assert 'Pumpkin' in content
    # check contents of draft
    draft_content = editor.draft_content(selenium.current_url)
    assert 'Pumpkin' in draft_content
    # save button enabled
    assert not page.is_save_button_disabled
    # discard
    page.discard()
