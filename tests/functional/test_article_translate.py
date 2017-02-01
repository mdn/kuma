import pytest

from pages.article_translate import TranslatePage
from pages.admin import AdminLogin


@pytest.mark.smoke
@pytest.mark.login
@pytest.mark.nondestructive
def test_translation(base_url, selenium):
    admin = AdminLogin(selenium, base_url).open()
    admin.login_moderator_user()
    page = TranslatePage(selenium, base_url, locale='fr').open()
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
