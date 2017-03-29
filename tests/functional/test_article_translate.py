import pytest

from pages.article_edit import EditPage
from pages.admin import AdminLogin
from utils.decorators import skip_if_maintenance_mode


@pytest.mark.smoke
@pytest.mark.login
@pytest.mark.nondestructive
@skip_if_maintenance_mode
def test_translation(base_url, selenium):
    admin = AdminLogin(selenium, base_url).open()
    admin.login_moderator_user()
    page = EditPage(selenium, base_url, locale='fr').open()
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
    # save button enabled
    assert not page.is_save_button_disabled
    # check contents of draft
    draft_content = editor.draft_content(selenium.current_url)
    assert 'Pumpkin' in draft_content
    # discard
    page.discard()
