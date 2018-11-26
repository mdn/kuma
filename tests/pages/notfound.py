from selenium.webdriver.common.by import By

from .base import BasePage


class NotFoundPage(BasePage):

    SLUG = 'skwiz'
    URL_TEMPLATE = '/{locale}/' + SLUG

    _page_title = (By.CSS_SELECTOR, '#content-main > h1')
    report_content_form_url = 'https://bugzilla.mozilla.org/form.doc'
    _report_content_locator = (By.CSS_SELECTOR,
                               '#content-main a[href^="' +
                               report_content_form_url + '"]')

    @property
    def loaded(self):
        return self.seed_url in self.selenium.current_url

    @property
    def page_title_text(self):
        page_title = self.find_element(*self._page_title)
        return page_title.text

    @property
    def is_report_link_displayed(self):
        article_report_link = self.find_element(*self._report_content_locator)
        return article_report_link.is_displayed()
