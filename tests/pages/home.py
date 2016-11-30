from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

from pages.base import BasePage
from pages.regions.column_container import ColumnContainer


class HomePage(BasePage):

    _masthead_locator = (By.CSS_SELECTOR, '.home-masthead')
    _masthead_search_locator = (By.ID, 'home-q')
    _column_callout_parent = (By.CSS_SELECTOR, '.home-callouts .column-container')
    _column_callout_locator = (By. CSS_SELECTOR, '.column-callout')
    _callout_links_locator = (By. CSS_SELECTOR, '.column-callout a')
    _hacks_link_locator = (By.CSS_SELECTOR, '.home-hacks .heading-link a')
    _hacks_items_locator = (By.CSS_SELECTOR, '.hentry')

    @property
    def is_masthead_displayed(self):
        return self.find_element(*self._masthead_locator).is_displayed()

    @property
    def masthead_search_input(self):
        return self.find_element(*self._masthead_search_locator)

    def search_for_term(self, term):
        masthead_search_input = self.find_element(*self._masthead_search_locator)
        masthead_search_input.send_keys('css', Keys.ENTER)
        from pages.search import SearchPage
        return SearchPage(self.selenium, self.base_url, term=term).wait_for_page_to_load()

    @property
    def callout_container(self):
        column_callout_parent = self.find_element(*self._column_callout_parent)
        return ColumnContainer(self, root=column_callout_parent)

    @property
    def callout_items_length(self):
        callout_items_list = self.find_elements(*self._column_callout_locator)
        callout_items_list_length = len(callout_items_list)
        return callout_items_list_length

    @property
    def callout_link_list(self):
        callout_link_list = self.find_elements(*self._callout_links_locator)
        return callout_link_list

    @property
    def hacks_url(self):
        hacks_link = self.find_element(*self._hacks_link_locator)
        return hacks_link.get_attribute('href')

    @property
    def hacks_items_length(self):
        hacks_items_list = self.find_elements(*self._hacks_items_locator)
        hacks_items_list_length = len(hacks_items_list)
        return hacks_items_list_length
