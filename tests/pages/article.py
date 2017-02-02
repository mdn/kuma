from selenium.webdriver.common.by import By

from pages.base import BasePage
import pages.article_edit
from pages.regions.column_container import ColumnContainer
from selenium.webdriver.common.action_chains import ActionChains


class ArticlePage(BasePage):

    URL_TEMPLATE = '/{locale}/docs/User:anonymous:uitest'

    # article meta
    _language_button_locator = (By.ID, 'languages-menu')
    _language_submenu_locator = (By.ID, 'languages-menu-submenu')
    _language_add_link_locator = (By.ID, 'translations-add')
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

    # page buttons
    @property
    def is_language_menu_displayed(self):
        return self.find_element(*self._language_button_locator).is_displayed()

    def trigger_add_translation(self):
        submenu_trigger = self.find_element(*self._language_button_locator)
        submenu = self.find_element(*self._language_submenu_locator)
        hover = ActionChains(self.selenium).move_to_element(submenu_trigger)
        hover.perform()
        self.wait.until(lambda s: submenu.is_displayed())
        add_translation = self.find_element(*self._language_add_link_locator)
        add_translation.click()
        self.wait.until(lambda s: '$locale' in s.current_url)

    @property
    def is_edit_button_displayed(self):
        return self.find_element(*self._edit_button_locator).is_displayed()

    def click_edit(self, signedin):
        edit_button = self.find_element(*self._edit_button_locator)
        edit_button.click()
        if (signedin):
            return pages.article_edit.EditPage(self.selenium, self.base_url).wait_for_page_to_load()
        else:
            self.wait.until(lambda s: 'users/signin' in s.current_url)

    @property
    def is_advanced_menu_displayed(self):
        return self.find_element(*self._advanced_button_locator).is_displayed()

    @property
    def article_column_container_region(self):
        article_column_container = self.find_element(*self._article_column_container)
        return ColumnContainer(self, root=article_column_container)

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

    # article wrapper is displayed
    @property
    def is_article_displayed(self):
        return self.find_element(*self._article_locator).is_displayed()

    # article links
    @property
    def article_link_list(self):
        return self.find_elements(*self._article_links_locator)
