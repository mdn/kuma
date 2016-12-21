import pytest

from pages.article_new import NewPage
from pages.admin import AdminLogin


@pytest.mark.smoke
@pytest.mark.login
def test_new(base_url, selenium):
    admin = AdminLogin(selenium, base_url).open()
    admin.login_moderator_user()
    page = NewPage(selenium, base_url).open()
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
    # write title
    page.write_title()
    # check slug updates
    assert page.is_slug_suggested
    # publish
    published_page = page.publish()
    # correct content published
    assert 'Pumpkin' in published_page.article_content()
    # needs a review, because it's new
    assert published_page.is_technical_review_needed
    assert published_page.is_editorial_review_needed
    # passes TOC test
    assert published_page.is_test_toc
