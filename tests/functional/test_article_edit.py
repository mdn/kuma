import pytest
import time

from pages.article import ArticlePage
from pages.article_new import NewPage
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
def test_editor(base_url, selenium):
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


@pytest.mark.login
@skip_if_maintenance_mode
def test_drafts(base_url, selenium):
    admin = AdminLogin(selenium, base_url).open()
    admin.login_moderator_user()
    # create new page
    new_page = NewPage(selenium, base_url).open()
    new_page.write_title()
    new_page_editor = new_page.editor()
    # check draft autosave is not enabled
    assert not new_page_editor.is_draft_status_displayed
    new_page_editor.edit_source('Create page.')
    # publish page
    published_page = new_page.publish()
    # edit page
    edit_page = published_page.click_edit(True)
    editor = edit_page.editor()
    editor.edit_source('Draft1')
    # draft UI reports save
    assert editor.is_draft_autosave_displayed
    # check draft contents
    draft_content = editor.draft_content(selenium.current_url)
    assert 'Draft1' in draft_content
    # refresh page
    selenium.refresh()
    refreshed_editor = edit_page.editor()
    # wait until recovery option found
    edit_page.wait.until(lambda s: refreshed_editor.is_draft_restore_displayed)
    # recover draft
    refreshed_editor.restore_draft()
    # check article contents match draft
    editor_content = editor.content_source()
    assert 'Draft1' in editor_content
    # publish page
    second_published_page = edit_page.save()
    # check rev_saved striped from URL
    second_published_page.wait.until(lambda s: 'rev_saved' not in selenium.current_url)
    # edit page
    second_edit_page = published_page.click_edit(True)
    second_editor = second_edit_page.editor()
    # check first draft was deleted after being published
    initial_second_draft_content = second_editor.draft_content(selenium.current_url)
    assert 'Draft1' not in initial_second_draft_content
    second_editor.edit_source('Draft2')
    # check draft contents
    second_draft_content = second_editor.draft_content(selenium.current_url)
    # check second draft saved
    assert 'Draft2' in second_draft_content
    # discard page (and with it second draft)
    second_publish = second_edit_page.discard()
    # edit page
    third_edit_page = second_publish.click_edit(True)
    third_editor = third_edit_page.editor()
    # check second draft discarded
    discarded_draft_content = third_editor.draft_content(selenium.current_url)
    assert 'Draft2' not in discarded_draft_content
    # edit third page
    third_editor.edit_source('Draft3')
    # refresh page
    selenium.refresh()
    refreshed_editor = third_edit_page.editor()
    # discard draft
    refreshed_editor.discard_draft()
    # check draft discarded
    refreshed_editor_draft_contents = refreshed_editor.draft_content(selenium.current_url)
    assert 'Draft3' not in refreshed_editor_draft_contents
    # check interface updated
    assert refreshed_editor.draft_discarded_status
    current_revision_id = third_edit_page.current_revision_id
    refreshed_editor.fake_old_draft(selenium.current_url, current_revision_id)
    # refresh page
    selenium.refresh()
    fake_draft_refreshed_editor = third_edit_page.editor()
    # check that saved draft was detected & reported as old, can't be restored
    assert fake_draft_refreshed_editor.is_draft_old_displayed
    assert fake_draft_refreshed_editor.is_draft_outdated
    assert not fake_draft_refreshed_editor.is_draft_restore_displayed
    # view saved draft
    fake_draft_refreshed_editor.view_draft()
    # give JS a second to do that
    time.sleep(0.5)
    # check view happened
    editor_content = fake_draft_refreshed_editor.content_source()
    assert 'Old draft' in editor_content
    # check publishing blocked as expected
    publish_old = third_edit_page.save()
    assert publish_old.is_error_list_displayed
