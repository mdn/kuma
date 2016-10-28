from selenium.webdriver.common.by import By

from pages.article import ArticlePage


class NotFoundPage(ArticlePage):

    URL_TEMPLATE = '/{locale}/skwiz'

    report_content_form_url = 'https://bugzilla.mozilla.org/form.doc'
    _report_content_locator = (By.CSS_SELECTOR,
                               '#content-main a[href^="' +
                               report_content_form_url + '"]')

    @property
    def is_report_link_displayed(self):
        article_report_link = self.find_element(*self._report_content_locator)
        return article_report_link.is_displayed()
