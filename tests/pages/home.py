from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

from pages.base import BasePage


class HomePage(BasePage):

    _masthead_locator = (By.CSS_SELECTOR, '.home-masthead')
    _masthead_search_locator = (By.ID, 'home-q')

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
