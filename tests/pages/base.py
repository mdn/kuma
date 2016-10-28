import re
from urlparse import urlparse, parse_qs
from braceexpand import braceexpand

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.select import Select
from selenium.webdriver.common.action_chains import ActionChains

from pypom import Page, Region

class BasePage(Page):

    URL_TEMPLATE = '/{locale}'

    def __init__(self, selenium, base_url, locale='en-US', **url_kwargs):
        super(BasePage, self).__init__(selenium, base_url, locale=locale, **url_kwargs)

    def wait_for_page_to_load(self):
        self.wait.until(lambda s: self.seed_url in s.current_url)
        el = self.find_element(By.TAG_NAME, 'html')
        self.wait.until(lambda s: el.get_attribute('data-ffo-opensanslight'))
        return self

    @property
    def header(self):
        return self.Header(self)

    @property
    def footer(self):
        return self.Footer(self)

    class Header(Region):
        report_content_form_url = 'https://bugzilla.mozilla.org/form.doc'
        report_bug_form_url = 'https://bugzilla.mozilla.org/form.mdn'
        # locators
        _root_locator = (By.ID, 'main-header')
        _menu_locator = (By.ID, 'nav-main-menu')
        _menu_top_links = (By.CSS_SELECTOR, '#main-nav > ul > li > a[href]')
        _platform_submenu_trigger_locator = (By.XPATH,
                                             'id(\'nav-platform-submenu\')/..')
        _platform_submenu_locator = (By.ID, 'nav-platform-submenu')
        _platform_submenu_link_locator = (By.CSS_SELECTOR,
                                          '#nav-platform-submenu a')
        _feedback_link_locator = (By.XPATH, 'id(\'nav-contact-submenu\')/../a')
        _feedback_submenu_trigger_locator = (By.XPATH,
                                             'id(\'nav-contact-submenu\')/..')
        _feedback_submenu_locator = (By.ID, 'nav-contact-submenu')
        _report_content_locator = (By.CSS_SELECTOR,
                                   'a[href^="' + report_content_form_url + '"]')
        _report_bug_locator = (By.CSS_SELECTOR,
                               'a[href^="' + report_bug_form_url + '"]')
        _search_field_locator = (By.ID, 'main-q')

        # is displayed?
        @property
        def is_displayed(self):
            return self.root.is_displayed()

        # nav is displayed?
        @property
        def is_menu_displayed(self):
            return self.find_element(*self._menu_locator).is_displayed()

        # top level links from navigation menu
        @property
        def menu_top_links_list(self):
            return self.find_element(*self._menu_top_links)

        # platform submenu
        @property
        def is_platform_submenu_trigger_displayed(self):
            submenu_trigger = self.find_element(*self._platform_submenu_trigger_locator)
            return submenu_trigger.is_displayed()

        @property
        def is_platform_submenu_displayed(self):
            submenu = self.find_element(*self._platform_submenu_locator)
            return submenu.is_displayed()

        def show_platform_submenu(self):
            submenu_trigger = self.find_element(*self._platform_submenu_trigger_locator)
            submenu = self.find_element(*self._platform_submenu_locator)
            hover = ActionChains(self.selenium).move_to_element(submenu_trigger)
            hover.perform()
            self.wait.until(lambda s: submenu.is_displayed())

        # feedback submenu
        @property
        def is_feedback_submenu_trigger_displayed(self):
            submenu_trigger = self.find_element(*self._feedback_submenu_trigger_locator)
            return submenu_trigger.is_displayed()

        @property
        def is_feedback_submenu_displayed(self):
            submenu = self.find_element(*self._feedback_submenu_locator)
            return submenu.is_displayed()

        @property
        def is_report_content_link_displayed(self):
            report_content_link = self.find_element(*self._report_content_locator)
            return report_content_link.is_displayed()

        @property
        def is_report_bug_link_displayed(self):
            report_bug_link = self.find_element(*self._report_bug_locator)
            return report_bug_link.is_displayed()

        def show_feedback_submenu(self):
            submenu_trigger = self.find_element(*self._feedback_submenu_trigger_locator)
            submenu = self.find_element(*self._feedback_submenu_locator)
            hover = ActionChains(self.selenium).move_to_element(submenu_trigger)
            hover.perform()
            self.wait.until(lambda s: submenu.is_displayed())

        def open_feedback(self, locale, path):
            self.find_element(*self._feedback_link_locator).click()
            from pages.article import ArticlePage
            return ArticlePage(self.selenium, self.page.base_url, locale, path=path).wait_for_page_to_load()

        def localized_feedback_path(self, locale):
            link = self.find_element(*self._feedback_link_locator)
            href = link.get_attribute('href')
            # base url may or may not be part of string
            path = re.sub(self.page.base_url, '', href)
            # if base url was not part of string there's a leading / to remove
            path = re.sub(r'^/', '', path)
            # remove locale and following /
            path = re.sub(r'^' + locale + '\/', '', path)
            return path

        def open_report_content(self):
            self.find_element(*self._report_content_locator).click()
            # TODO - what to return???
            # return FeedbackPage(self.selenium, self.page.base_url).wait_for_page_to_load()

        def is_report_content_url_expected(self, selenium, article_url):
            current_url = selenium.current_url
            report_url = self.report_content_form_url
            # current_url_simplified = re.sub(r'[^a-zA-Z]', '', current_url)
            # article_url_simplified = re.sub(r'[^a-zA-Z]', '', article_url)
            # compare
            url_matches = report_url in current_url
            # url_contains_article = article_url_simplified in current_url_simplified
            return url_matches

        def open_report_bug(self):
            self.find_element(*self._report_bug_locator).click()

        def is_report_bug_url_expected(self, selenium):
            return self.report_bug_form_url in selenium.current_url

        @property
        def search_field_width(self):
            search_field = self.find_element(*self._search_field_locator)
            return search_field.size['width']

        def search_field_focus(self):
            plaform_submenu_trigger  = self.find_element(*self._platform_submenu_trigger_locator)
            search_field = self.find_element(*self._search_field_locator)
            focus = ActionChains(self.selenium).move_to_element(search_field).click()
            focus.perform()
            self.wait.until(lambda s: not plaform_submenu_trigger.is_displayed())

        def search_for_term(self, term):
            search_field = self.find_element(*self._search_field_locator)
            search_field.send_keys('css', Keys.ENTER)
            from pages.search import SearchPage
            return SearchPage(self.selenium, self.page.base_url, term=term).wait_for_page_to_load()

    class Footer(Region):
        privacy_url = 'https://www.mozilla.org/privacy/websites/'
        copyright_url = '/docs/MDN/About#Copyrights_and_licenses'
        # locators
        _root_locator = (By.CSS_SELECTOR, 'body > footer')
        _language_locator = (By.ID, 'language')
        _privacy_locator = (By.CSS_SELECTOR, 'a[href^="' + privacy_url + '"]')
        _license_locator = (By.CSS_SELECTOR, 'a[href="' + copyright_url + '"]')

        # is displayed?
        @property
        def is_displayed(self):
            return self.root.is_displayed()

        # language select is displayed
        @property
        def is_select_language_displayed(self):
            return self.find_element(*self._language_locator).is_displayed()

        # check language selected locale
        @property
        def language_value(self):
            # get language selected
            language_select = self.find_element(*self._language_locator)
            selected_option = language_select.find_element(By.CSS_SELECTOR, 'option[selected]')
            selected_language = selected_option.get_attribute('value')
            return selected_language

        def select_language(self, value):
            language_select = self.find_element(*self._language_locator)
            Select(language_select).select_by_value(value)
            self.wait.until(lambda s: '/{0}/'.format(value) in s.current_url)

        # privacy link is displayed
        @property
        def is_privacy_displayed(self):
            return self.find_element(*self._privacy_locator).is_displayed()

        # license link is displayed
        @property
        def is_license_displayed(self):
            return self.find_element(*self._license_locator).is_displayed()
