import datetime
import time
from selenium.webdriver.common.by import By

from pages.article_edit import EditPage


class NewPage(EditPage):

    URL_TEMPLATE = '/{locale}/docs/new'
    DOC_SLUG = datetime.datetime.now().strftime("%Y%m%d%H%M%S")

    _title_input_locator = (By.ID, 'id_title')
    _slug_input_locator = (By.ID, 'id_slug')

    def publish(self):
        # short wait to allow save button to be enabled
        # dirtiness tracking only fires every 1.5 seconds
        time.sleep(1.6)
        from pages.article import ArticlePage
        publish_button = self.find_element(*self._save_button_locator)
        publish_button.click()
        # wait for article page to load
        published_page = ArticlePage(
            self.selenium,
            self.base_url,
            locale=self.DEFAULT_LOCALE,
            slug=self.DOC_SLUG,
        )
        return published_page.wait_for_page_to_load()

    def write_title(self):
        title_input = self.find_element(*self._title_input_locator)
        title_input.send_keys(self.DOC_SLUG)
        slug_input = self.find_element(*self._slug_input_locator)
        self.wait.until(
            lambda s: slug_input.get_attribute('value') in self.DOC_SLUG
        )

    @property
    def is_slug_suggested(self):
        slug_input = self.find_element(*self._slug_input_locator)
        slug_value = slug_input.get_attribute('value')
        return slug_value in self.DOC_SLUG
