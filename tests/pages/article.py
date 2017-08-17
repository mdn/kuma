from selenium.webdriver.common.by import By

from pages.base import BasePage
from pages.regions.column_container import ColumnContainer
from selenium.webdriver.common.action_chains import ActionChains


class ArticlePage(BasePage):
    """A non-zone MDN wiki page."""

    URL_TEMPLATE = '/{locale}/docs/{slug}'
    DEFAULT_LOCALE = 'en-US'
    DEFAULT_SLUG = 'User:anonymous:uitest'

    # article meta
    _language_add_link_locator = (By.ID, 'translations-add')
    _edit_button_locator = (By.ID, 'edit-button')
    _advanced_button_locator = (By.ID, 'advanced-menu')
    # article head
    _article_title_locator = (By.CSS_SELECTOR, '.document-head h1')
    # article columns
    _article_column_container_locator = (By.ID, 'wiki-column-container')
    _article_left_column_locator = (By.ID, 'wiki-left')
    _article_content_column_locator = (By.ID, 'wiki-content')
    # article
    _article_locator = (By.ID, 'wikiArticle')
    _article_links_locator = (By.CSS_SELECTOR, '#wikiArticle a[href]')
    # review links
    _technical_review_link_locator = (By.CSS_SELECTOR, 'a[href$=Do_a_technical_review]')
    _editorial_review_link_locator = (By.CSS_SELECTOR, 'a[href$=Do_an_editorial_review]')
    # table of contents
    _toc_locator = (By.ID, 'toc')
    # error list
    _error_list = (By.CSS_SELECTOR, '.errorlist')

    def __init__(self, *args, **kwargs):
        locale = kwargs.pop('locale', self.DEFAULT_LOCALE)
        slug = kwargs.pop('slug', self.DEFAULT_SLUG)
        super(ArticlePage, self).__init__(locale=locale, slug=slug,
                                          *args, **kwargs)

    # article title
    @property
    def article_title_text(self):
        article_title = self.find_element(*self._article_title_locator)
        return article_title.text

    # page buttons
    @property
    def language_menu_button(self):
        return self.find_element(By.ID, 'languages-menu')

    @property
    def add_translation_link(self):
        return self.find_element(By.ID, 'translations-add')

    @property
    def is_language_menu_displayed(self):
        return self.language_menu_button.is_displayed()

    def display_language_menu(self):
        submenu_trigger = self.language_menu_button
        submenu = self.find_element(By.ID, 'languages-menu-submenu')
        hover = ActionChains(self.selenium).move_to_element(submenu_trigger)
        hover.perform()
        self.wait.until(lambda s: submenu.is_displayed())

    def trigger_add_translation(self):
        self.display_language_menu()
        self.add_translation_link.click()
        self.wait.until(lambda s: '$locale' in s.current_url)

    @property
    def is_add_translation_link_available(self):
        self.display_language_menu()
        self.add_translation_link.is_displayed()

    @property
    def has_edit_button(self):
        return len(self.find_elements(*self._edit_button_locator)) > 0

    @property
    def is_edit_button_displayed(self):
        return self.find_element(*self._edit_button_locator).is_displayed()

    def click_edit(self, signedin):
        from pages.article_edit import EditPage
        edit_button = self.find_element(*self._edit_button_locator)
        edit_button.click()
        if (signedin):
            edit_page = EditPage(
                self.selenium,
                self.base_url,
                **self.url_kwargs
            )
            return edit_page.wait_for_page_to_load()
        else:
            self.wait.until(lambda s: 'users/signin' in s.current_url)

    @property
    def is_advanced_menu_displayed(self):
        return self.find_element(*self._advanced_button_locator).is_displayed()

    @property
    def article_column_container_region(self):
        article_column_container = self.find_element(*self._article_column_container_locator)
        return ColumnContainer(self, root=article_column_container)

    # article columns
    @property
    def is_article_column_left_present(self):
        column_container = self.find_element(*self._article_column_container_locator)
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

    # article wrapper is displayed
    @property
    def is_article_displayed(self):
        return self.find_element(*self._article_locator).is_displayed()

    def article_content(self):
        return self.find_element(*self._article_locator).text

    # article links
    @property
    def article_link_list(self):
        return self.find_elements(*self._article_links_locator)

    # technical review
    @property
    def is_technical_review_needed(self):
        return self.find_elements(*self._technical_review_link_locator)

    # editorial review
    @property
    def is_editorial_review_needed(self):
        return self.find_elements(*self._editorial_review_link_locator)

    # toc
    @property
    def is_test_toc(self):
        # this is looking for the TOC generated by TEXT_TEXT defined in pages.regions.ckeditor
        self.find_elements(*self._toc_locator)
        # check heading two
        heading_two_link = self.find_element(By.CSS_SELECTOR, 'a[href="#Heading_Two"]').is_displayed()
        heading_two_anchor = self.find_element(By.ID, 'Heading_Two').is_displayed()
        # check heading three
        heading_three_link = self.find_element(By.CSS_SELECTOR, 'a[href="#Heading_Three"]').is_displayed()
        heading_three_anchor = self.find_element(By.ID, 'Heading_Three').is_displayed()
        return heading_two_link and heading_two_anchor and heading_three_link and heading_three_anchor

    # error list
    @property
    def is_error_list_displayed(self):
        error_list = self.find_element(*self._error_list)
        return error_list.is_displayed()
