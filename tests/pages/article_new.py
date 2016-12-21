import datetime
from pypom import Region
from selenium.webdriver.common.by import By

from pages.base import BasePage
import pages.article
from pages.regions.ckeditor import Ckeditor


class NewPage(BasePage):

    URL_TEMPLATE = '/{locale}/docs/new'
    CKEDITOR_READY_QUERY = "return window.CKEDITOR.instances.id_content.status === 'ready';"
    DOC_SLUG = datetime.datetime.now().strftime("%Y%m%d%H%M%S")

    def wait_for_page_to_load(self):
        el = self.find_element(By.TAG_NAME, 'html')
        self.wait.until(lambda s: el.get_attribute('data-ffo-opensanslight'))
        # also wait for ckeditor to load
        self.wait.until(lambda s: s.execute_script(self.CKEDITOR_READY_QUERY) is True)
        return self

    _title_input_locator = (By.ID, 'id_title')
    _slug_input_locator = (By.ID, 'id_slug')
    _ckeditor_wrapper_locator = (By.ID, 'editor-wrapper')
    _draft_container_locator = (By.CSS_SELECTOR, '.draft-container')
    _save_and_keep_editing_button_locator = (By.CSS_SELECTOR, '.btn-save-and-edi')
    _save_button_locator = (By.CSS_SELECTOR, '.btn-save')
    _discard_button_locator = (By.CSS_SELECTOR, '.btn-discard')

    @property
    def is_save_button_disabled(self):
        save_button = self.find_element(*self._save_button_locator)
        return save_button.get_attribute('disabled') is not None

    def discard(self):
        discard_button = self.find_element(*self._discard_button_locator)
        discard_button.click()
        # wait for article page to load
        return pages.article.ArticlePage(self.selenium, self.base_url).wait_for_page_to_load()

    def publish(self):
        publish_button = self.find_element(*self._save_button_locator)
        publish_button.click()
        # wait for article page to load
        return pages.article.ArticlePage(self.selenium, self.base_url).wait_for_page_to_load()

    def write_title(self):
        title_input = self.find_element(*self._title_input_locator)
        title_input.send_keys(self.DOC_SLUG)
        slug_input = self.find_element(*self._slug_input_locator)
        self.wait.until(lambda s: slug_input.get_attribute('value') in self.DOC_SLUG)

    @property
    def is_slug_suggested(self):
        slug_input = self.find_element(*self._slug_input_locator)
        slug_value = slug_input.get_attribute('value')
        return slug_value in self.DOC_SLUG

    # CKEditor region
    def editor(self):
        editor_wrapper = self.find_element(*self._ckeditor_wrapper_locator)
        return Ckeditor(self, root=editor_wrapper)

    # check jQuery object has had tagit plugin functions attached
    def tagit_loaded(self):
        tagit_exists = self.selenium.execute_script("return typeof(jQuery.fn.tagit) == 'function'")
        return tagit_exists
