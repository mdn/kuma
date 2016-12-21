from urlparse import urlparse

from pypom import Region
from selenium.webdriver.common.by import By


class Ckeditor(Region):

    CKEDITOR_READY_QUERY = 'return window.CKEDITOR.instances.id_content.status === "ready";'
    CKEDITOR_CONTENT_QUERY = 'return window.CKEDITOR.instances["id_content"].getData();'

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
        parse_base_url = urlparse(base_url)
        draft_name = 'draft/edit' + parse_base_url.path.replace('$edit', '')
        draft_content_query = 'return localStorage.getItem("' + draft_name + '");'
        draft_content = self.selenium.execute_script(draft_content_query)
        return draft_content

    def edit_source(self):
        # switch to source mode
        source_button = self.find_element(*self._source_button_locator)
        source_button.click()
        self.wait.until(lambda s: self.find_element(*self._source_textarea_locator))
        # send keys
        source_textarea = self.find_element(*self._source_textarea_locator)
        edit_text = '<p>Pumpkin</p><iframe src="test.html"></iframe>';
        source_textarea.send_keys(edit_text)
        # switch out of source mode
        source_button.click()
        self.wait.until(lambda s: self.find_element(*self._wysiwyg_frame_locator))
        # wait until draft saved
        self.wait.until(lambda s: self.find_element(*self._draft_action_locator))
