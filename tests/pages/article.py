from pypom import Region
from selenium.webdriver.common.by import By

from pages.base import BasePage


class ArticlePage(BasePage):

    URL_TEMPLATE = '/{locale}/{path}'

    # article meta
    _language_button_locator = (By.ID, 'languages-menu')
    _language_submenu_locator = (By.ID, 'languages-menu-submenu')
    _edit_button_locator = (By.ID, 'edit-button')
    _advanced_button_locator = (By.ID, 'advanced-menu')
    # article head
    _article_title_locator = (By.CSS_SELECTOR, '#wiki-document-head h1')
    # article columns
    _article_column_container = (By.ID, 'wiki-column-container')
    _article_left_column_locator = (By.ID, 'wiki-left')
    _article_content_column_locator = (By.ID, 'wiki-content')
    _article_right_column_locator = (By.ID, 'wiki-right')
    # article
    _article_locator = (By.ID, 'wikiArticle')
    _article_links_locator = (By.CSS_SELECTOR, '#wikiArticle a[href]')

    # article title
    @property
    def article_title_text(self):
        article_title = self.find_element(*self._article_title_locator)
        return article_title.text

    # page buttons are displayed
    @property
    def is_language_menu_displayed(self):
        return self.find_element(*self._language_button_locator).is_displayed()

    @property
    def is_edit_button_displayed(self):
        return self.find_element(*self._edit_button_locator).is_displayed()

    @property
    def is_advanced_menu_displayed(self):
        return self.find_element(*self._advanced_button_locator).is_displayed()

    # article columns
    @property
    def is_article_column_left_present(self):
        column_container = self.find_element(*self._article_column_container)
        column_container_class = column_container.get_attribute('class')
        left_column = self.find_element(*self._article_left_column_locator)
        # parent container expects left
        left_expected = 'wiki-left-present' in column_container_class
        # left column is present
        left_present = left_column.is_displayed()
        return left_expected and left_present

    @property
    def is_article_column_content_present(self):
        content_column = self.find_element(*self._article_content_column_locator)
        return content_column.is_displayed()

    @property
    def article_column_right_present(self):
        column_container = self.find_element(*self._article_column_container)
        column_container_class = column_container.get_attribute('class')
        right_column = self.find_element(*self._article_right_column_locator)
        # parent container expects right
        right_expected = 'wiki-right-present' in column_container_class
        # right column is present
        right_present = right_column.is_displayed()
        return right_expected and right_present

    @property
    def is_article_columns_expected_layout(self):
        left_column = self.find_element(*self._article_left_column_locator)
        content_column = self.find_element(*self._article_content_column_locator)
        right_column = self.find_element(*self._article_right_column_locator)

        left_column_location = left_column.location
        content_column_location = content_column.location
        right_column_location = right_column.location

        left_column_y = left_column_location['y']
        content_column_y = content_column_location['y']
        right_column_y = right_column_location['y']

        left_column_x = left_column_location['x']
        content_column_x = content_column_location['x']
        right_column_x = right_column_location['x']

        # check y coordinates all the same
        y_match = left_column_y == content_column_y == right_column_y
        # check x coordinates are acsending
        x_acsend = left_column_x < content_column_x < right_column_x
        return y_match and x_acsend

    # article wrapper is displayed
    @property
    def is_article_displayed(self):
        return self.find_element(*self._article_locator).is_displayed()

    # article links
    @property
    def article_link_list(self):
        return self.find_elements(*self._article_links_locator)
