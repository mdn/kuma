from pypom import Region
from selenium.webdriver.common.by import By

from pages.base import BasePage


class SearchPage(BasePage):

    URL_TEMPLATE = '/{locale}/search?q={term}'

    _search_input_locator = (By.ID, 'search-q')
    _results_list_locator = (By.CSS_SELECTOR, '.result-list')
    _results_items_locator = (By.CSS_SELECTOR, '.result-list-item')
    _results_links_locator = (By.CSS_SELECTOR, '.result-list-item h4 a')
    _next_button_locator = (By.ID, 'search-result-next')
    # filters
    _all_topics_filter_checkbox_locator = (By.CSS_SELECTOR, '.search-results-filters input[value="none"]')
    _all_topics_filter_label_locator = (By.CSS_SELECTOR, '.search-results-filters > fieldset > label')
    _css_filter_checkbox_locator = (By.CSS_SELECTOR, '.search-results-filters input[value="css"]')
    _html_filter_checkbox_locator = (By.CSS_SELECTOR, '.search-results-filters input[value="html"]')
    _javascript_filter_checkbox_locator = (By.CSS_SELECTOR, '.search-results-filters input[value="js"]')
    # layout
    _results_explanation_locator = (By.CSS_SELECTOR, '#content .search-results-explanation')
    _results_explanation_p_locator = (By.CSS_SELECTOR, '#content .search-results-explanation p')
    _main_column_locator = (By.CSS_SELECTOR, '#content .column-main')
    _side_column_locator = (By.CSS_SELECTOR, '#content .column-strip')

    @property
    def search_input_value(self):
        return self.find_element(*self._search_input_locator).get_attribute('value')

    @property
    def search_result_items_length(self):
        results_items_list = self.find_elements(*self._results_items_locator)
        results_items_list_length = len(results_items_list)
        return results_items_list_length

    @property
    def search_results_link_list(self):
        results_link_list = self.find_elements(*self._results_links_locator)
        return results_link_list

    @property
    def is_next_button_displayed(self):
        next_button = self.find_element(*self._next_button_locator)
        return next_button.is_displayed()

    @property
    def is_css_filter_checked(self):
        css_filter = self.find_element(*self._css_filter_checkbox_locator)
        return css_filter.is_selected()

    @property
    def is_html_filter_checked(self):
        html_filter = self.find_element(*self._html_filter_checkbox_locator)
        return html_filter.is_selected()

    @property
    def is_javascript_filter_checked(self):
        javascript_filter = self.find_element(*self._javascript_filter_checkbox_locator)
        return javascript_filter.is_selected()

    def search_all_topics(self):
        all_topics_filter_label = self.find_element(*self._all_topics_filter_label_locator)
        all_topics_filter_label.click()
        self.wait.until(lambda s: 'none=none' in s.current_url)

    @property
    def is_results_explanation_displayed(self):
        results_explanation = self.find_element(*self._results_explanation_locator)
        return results_explanation.is_displayed()

    @property
    def documents_found(self):
        results_explanation_text = self.find_element(*self._results_explanation_p_locator).text
        documents_found = results_explanation_text.split(' ')[0]
        return documents_found

    @property
    def is_main_column_present(self):
        main_column = self.find_element(*self._main_column_locator)
        return main_column.is_displayed()

    @property
    def is_side_column_present(self):
        side_column = self.find_element(*self._side_column_locator)
        return side_column.is_displayed()

    @property
    def is_article_columns_expected_layout(self):
        main_column = self.find_element(*self._main_column_locator)
        side_column = self.find_element(*self._side_column_locator)

        main_column_location = main_column.location
        side_column_location = side_column.location

        main_column_y = main_column_location['y']
        side_column_y = side_column_location['y']

        main_column_x = main_column_location['x']
        side_column_x = side_column_location['x']

        # check y coordinates all the same
        y_match = main_column_y == side_column_y
        # check x coordinates are acsending
        x_acsend = main_column_x < side_column_x
        return y_match and x_acsend
