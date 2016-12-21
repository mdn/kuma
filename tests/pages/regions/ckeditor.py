from urlparse import urlparse

from pypom import Region
from selenium.webdriver.common.by import By


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
    _content_textarea_locator = (By.ID, 'id_content')
    _draft_action_locator = (By.ID, 'draft-action')
    _wysiwyg_frame_locator = (By.CSS_SELECTOR, '.cke_wysiwyg_frame')
    _source_button_locator = (By.CSS_SELECTOR, '.cke_button__source')
    _source_textarea_locator = (By.CSS_SELECTOR, '.cke_source')

    @property
    def ready(self):
        ready = self.selenium.execute_script(self.CKEDITOR_READY_QUERY)
        return ready

    def content_source(self):
        return self.selenium.execute_script(self.CKEDITOR_CONTENT_QUERY)

    def draft_content(self, base_url):
        # remove domain from base url
        url = urlparse(base_url)
        if url.path.startswith('/en-US/docs/new'):
            draft_name = 'draft/new'
        else:
            url_strip_edit = url.path.replace('$edit', '')
            # check if this is a regular edit page or translation
            if not url.path.startswith('/en-US/'):
                draft_name = 'draft/translate{}/'.format(url_strip_edit)
            else:
                draft_name = 'draft/edit' + url_strip_edit
        return self.selenium.execute_script(
            'return localStorage.getItem("{}");'.format(draft_name)
        )

    def edit_source(self):
        # switch to source mode
        source_button = self.find_element(*self._source_button_locator)
        source_button.click()
        self.wait.until(lambda s: self.find_element(*self._source_textarea_locator))
        # send keys
        source_textarea = self.find_element(*self._source_textarea_locator)
        edit_text = self.TEST_TEXT
        source_textarea.send_keys(edit_text)
        # switch out of source mode
        source_button.click()
        self.wait.until(lambda s: self.find_element(*self._wysiwyg_frame_locator))
        # wait until draft saved
        self.wait.until(lambda s: self.find_element(*self._draft_action_locator))
