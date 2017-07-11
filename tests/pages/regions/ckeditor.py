import time
from urlparse import urlparse

from pypom import Region
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException


class Ckeditor(Region):

    CKEDITOR_READY_QUERY = 'return window.CKEDITOR.instances.id_content.status === "ready";'
    CKEDITOR_CONTENT_QUERY = 'return window.CKEDITOR.instances["id_content"].getData();'

    TEST_TEXT = ('<p>Pumpkin is an unusual word that shouldn\'t already be on the page.</p>'
                 '<h2>Heading Two</h2>'
                 '<p>Paragraph for heading two.</p>'
                 '<h3>Heading Three</h3>'
                 '<p>Paragraph for heading three.</p>'
                 '<iframe src="test.html"></iframe>')

    _root_locator = (By.ID, 'editor-wrapper')
    _draft_container_locator = (By.CSS_SELECTOR, '.draft-container')
    _draft_old_locator = (By.CSS_SELECTOR, '.draft-old')
    _draft_restore_locator = (By.CSS_SELECTOR, '.js-restoreLink')
    _draft_discard_locator = (By.CSS_SELECTOR, '.js-discardLink')
    _draft_view_locator = (By.CSS_SELECTOR, '.js-viewLink')
    _draft_status_locator = (By.CSS_SELECTOR, '.draft-status')
    _draft_action_locator = (By.ID, 'draft-action')
    _draft_old_locator = (By.CSS_SELECTOR, '.draft-old')
    _wysiwyg_frame_locator = (By.CSS_SELECTOR, '.cke_wysiwyg_frame')
    _source_button_locator = (By.CSS_SELECTOR, '.cke_button__source')
    _source_textarea_locator = (By.CSS_SELECTOR, '.cke_source')

    @property
    def ready(self):
        ready = self.selenium.execute_script(self.CKEDITOR_READY_QUERY)
        return ready

    def content_source(self):
        return self.selenium.execute_script(self.CKEDITOR_CONTENT_QUERY)

    def draft_slug(self, draft_url):
        # remove domain from base url
        # TODO this function does not work for drafts for new translations
        url = urlparse(draft_url)
        url_strip_edit = url.path.replace('$edit', '')
        return 'draft/edit' + url_strip_edit

    @property
    def is_draft_container_displayed(self):
        try:
            self.find_element(*self._draft_container_locator).is_displayed()
        except NoSuchElementException:
            return False

    @property
    def is_draft_old_displayed(self):
        try:
            return self.find_element(*self._draft_old_locator).is_displayed()
        except NoSuchElementException:
            return False

    @property
    def is_draft_outdated(self):
        old_draft = self.find_element(*self._draft_old_locator)
        return 'you will not be able to submit it' in old_draft.text

    @property
    def is_draft_restore_displayed(self):
        try:
            return self.find_element(
                *self._draft_restore_locator
            ).is_displayed()
        except NoSuchElementException:
            return False

    def restore_draft(self):
        restore = self.find_element(*self._draft_restore_locator)
        restore.click()

    def discard_draft(self):
        discard = self.find_element(*self._draft_discard_locator)
        discard.click()

    def view_draft(self):
        discard = self.find_element(*self._draft_view_locator)
        discard.click()

    def draft_discarded_status(self):
        old_draft_status = self.find_element(*self._draft_old_locator)
        return 'Draft discarded' in old_draft_status.text

    @property
    def is_draft_status_displayed(self):
        try:
            return self.find_element(*self._draft_status_locator).is_displayed()
        except NoSuchElementException:
            return False

    @property
    def is_draft_autosave_displayed(self):
        action = self.find_element(*self._draft_action_locator)
        return 'autosaved' in action.text

    def draft_content(self, base_url):
        draft_name = self.draft_slug(base_url)
        draft = self.selenium.execute_script(
            'return localStorage.getItem("{}");'.format(draft_name)
        )
        if (draft is None):
            return ''
        else:
            return draft

    def edit_source(self, content=TEST_TEXT):
        # switch to source mode
        source_button = self.find_element(*self._source_button_locator)
        source_button.click()
        self.wait.until(lambda s: self.find_element(*self._source_textarea_locator))
        # send keys
        source_textarea = self.find_element(*self._source_textarea_locator)
        edit_text = content
        source_textarea.send_keys(edit_text)
        # switch out of source mode
        source_button.click()
        # short wait for drafts function debounce to kick in
        time.sleep(0.5)
        self.wait.until(lambda s: self.find_element(*self._wysiwyg_frame_locator))

    def fake_old_draft(self, article_url, revision_id):
        fake_content = 'Old draft.'
        fake_time = '2015-10-21 7:28:00 PM'
        # server 500s if revision is not in database
        # guess at existing revision by subtracting 1 from one we know exists
        fake_revision = int(revision_id) - 1
        draft_name = self.draft_slug(article_url)
        # construct javascript
        fake_content_script = 'localStorage.setItem("' + draft_name + '", "' + fake_content + '")'
        fake_time_script = 'localStorage.setItem("' + draft_name + '#save-time", "' + fake_time + '")'
        fake_revision_script = 'localStorage.setItem("' + draft_name + '#revision", "' + str(fake_revision) + '")'
        # execute javascript
        self.selenium.execute_script(fake_content_script)
        self.selenium.execute_script(fake_time_script)
        self.selenium.execute_script(fake_revision_script)
