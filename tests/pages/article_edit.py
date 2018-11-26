import time

from selenium.webdriver.common.by import By

from .base import BasePage
from .regions.ckeditor import Ckeditor


class EditPage(BasePage):

    URL_TEMPLATE = '/{locale}/docs/{slug}$edit'
    DEFAULT_LOCALE = 'en-US'
    DEFAULT_SLUG = 'User:anonymous:uitest'
    CKEDITOR_READY_QUERY = (
        "return window.CKEDITOR.instances.id_content.status === 'ready';"
    )

    _first_contrib_welcome_locator = (By.CSS_SELECTOR, '.first-contrib-welcome')
    _revision_id = (By.ID, 'id_current_rev')
    _ckeditor_wrapper_locator = (By.ID, 'editor-wrapper')
    _save_button_locator = (By.CSS_SELECTOR, '.btn-save')
    _discard_button_locator = (By.CSS_SELECTOR, '.btn-discard')

    def __init__(self, *args, **kwargs):
        locale = kwargs.pop('locale', self.DEFAULT_LOCALE)
        slug = kwargs.pop('slug', self.DEFAULT_SLUG)
        super(EditPage, self).__init__(locale=locale, slug=slug,
                                       *args, **kwargs)

    @property
    def is_save_button_disabled(self):
        save_button = self.find_element(*self._save_button_locator)
        return save_button.get_attribute('disabled') is not None

    # contributor welcome message displayed
    @property
    def is_first_contrib_welcome_displayed(self):
        return self.find_element(
            *self._first_contrib_welcome_locator
        ).is_displayed()

    # check jQuery object has had tagit plugin functions attached
    @property
    def tagit_loaded(self):
        tagit_exists = self.selenium.execute_script(
            "return typeof(jQuery.fn.tagit) == 'function'"
        )
        return tagit_exists

    @property
    def loaded(self):
        # also wait for ckeditor to load
        return ((self.seed_url in self.selenium.current_url) and (
            self.wait.until(
                lambda s: s.execute_script(self.CKEDITOR_READY_QUERY)
            )
        ))

    @property
    def current_revision_id(self):
        revision_id = self.find_element(*self._revision_id)
        return revision_id.get_attribute('value')

    # CKEditor region
    def editor(self):
        editor_wrapper = self.find_element(*self._ckeditor_wrapper_locator)
        return Ckeditor(self, root=editor_wrapper)

    def save(self):
        # short wait to allow save button to be enabled
        # dirtiness tracking only fires every 1.5 seconds
        time.sleep(1.6)
        from pages.article import ArticlePage
        save_button = self.find_element(*self._save_button_locator)
        save_button.click()
        # wait for article page to load
        return ArticlePage(
            self.selenium,
            self.base_url,
            **self.url_kwargs
        ).wait_for_page_to_load()

    def discard(self):
        from pages.article import ArticlePage
        discard_button = self.find_element(*self._discard_button_locator)
        discard_button.click()
        # wait for article page to load
        return ArticlePage(
            self.selenium,
            self.base_url,
            **self.url_kwargs
        ).wait_for_page_to_load()
