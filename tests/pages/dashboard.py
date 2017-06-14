from pypom import Region
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

from pages.base import BasePage


class DashboardPage(BasePage):

    URL_TEMPLATE = '/{locale}/dashboards/revisions'

    _revision_filter_form_locator = (By.ID, 'revision-filter')
    _revision_page_input = (By.ID, 'revision-page')
    _notification_tray_locator = (By.CSS_SELECTOR, '.notification-tray')
    _first_notification_locator = (By.CSS_SELECTOR, '.notification-tray .notification:first-child')
    _parent_locator = (By.ID, 'revision-replace-block')
    _pagination_locator = (By.CSS_SELECTOR, '.pagination')
    _page_two_link = (By.CSS_SELECTOR, '.pagination > li:first-child + li a')
    _ip_toggle_locator = (By.ID, 'show_ips_btn')
    _first_row_locator = (By.CSS_SELECTOR,
                          '.dashboard-table tbody .dashboard-row:first-child')
    _first_details_locator = (By.CSS_SELECTOR,
                              '.dashboard-table tbody .dashboard-row:first-child + .dashboard-detail')
    _first_details_diff_locator = (By.CSS_SELECTOR,
                                   '.dashboard-table tbody .dashboard-row:first-child + .dashboard-detail .diff')
    _details_locator = (By.CSS_SELECTOR, '.dashboard-detail')

    @property
    def is_ip_toggle_present(self):
        try:
            self.find_element(*self._ip_toggle_locator)
            return True
        except:
            return False

    @property
    def first_row(self):
        first_row = self.find_element(*self._first_row_locator)
        return DashboardRow(self, root=first_row)

    @property
    def first_row_id(self):
        return self.find_element(*self._first_row_locator).get_attribute('data-revision-id')

    @property
    def details_items_length(self):
        details_items = self.find_elements(*self._details_locator)
        return len(details_items)

    def open_first_details(self):
        first_row = self.find_element(*self._first_row_locator)
        first_row.click()
        self.wait.until(lambda s: len(self.find_elements(*self._details_locator)) > 0)

    @property
    def is_first_details_displayed(self):
        first_details = self.find_element(*self._first_details_locator)
        return first_details.is_displayed()

    @property
    def is_first_details_diff_displayed(self):
        first_details_diff = self.find_element(*self._first_details_diff_locator)
        return first_details_diff.is_displayed()

    def click_page_two(self):
        revision_filter_form = self.find_element(*self._revision_filter_form_locator)
        page_two_link = self.find_element(*self._page_two_link)
        page_two_link.click()
        # revsion-page updates to not 1
        self.wait.until(lambda s: int(self.find_element(*self._revision_page_input).get_attribute('value')) is not 1)
        # form is disabled when ajax request made
        self.wait.until(lambda s: 'disabled' in revision_filter_form.get_attribute('class'))
        # wait for tray to be added
        self.wait.until(lambda s: len(self.find_elements(*self._notification_tray_locator)) > 0)
        # wait for notification in tray
        self.wait.until(lambda s: len(self.find_elements(*self._first_notification_locator)) > 0)

        # form editable when ajax response arrives
        # This fails 40% of the time w/ default timeout of 10s
        # bug 1246164 - Redesign revision pagination for performance
        # http://selenium-python.readthedocs.io/waits.html#explicit-waits
        WebDriverWait(self.selenium, 30).until(lambda s: 'disabled' not in revision_filter_form.get_attribute('class'))

        # wait for notification to close
        self.wait.until(lambda s: 'closed' in self.find_element(*self._first_notification_locator).get_attribute('class'))
        # revsion-page-value updates to 1
        self.wait.until(lambda s: int(self.find_element(*self._revision_page_input).get_attribute('value')) == 1)
        # opacity maniulation finishes
        self.wait.until(lambda s: 'opacity' not in self.find_element(*self._parent_locator).get_attribute('style'))

    @property
    def dashboard_not_overflowing(self):
        crawlBar = self.selenium.execute_script("return document.documentElement.scrollWidth>document.documentElement.clientWidth;")
        return not crawlBar


class DashboardRow(Region):

    _root_locator = (By.CSS_SELECTOR, '.dashboard-row')
    _ban_ip_locator = (By.CSS_SELECTOR, '.dashboard-ban-ip-link')
    _spam_ham_button_locator = (By.CSS_SELECTOR, '.spam-ham-button')

    @property
    def revision_id(self):
        return self.root.get_attribute('data-revision-id')

    @property
    def is_ip_ban_present(self):
        try:
            self.find_element(*self._ban_ip_locator)
            return True
        except:
            return False

    @property
    def is_spam_ham_button_present(self):
        try:
            self.find_element(*self._spam_ham_button_locator)
            return True
        except:
            return False


class DashboardDetail(Region):

    _root_locator = (By.CSS_SELECTOR, '.dashboard-detail')
    _page_buttons_locator = (By.CSS_SELECTOR, '.page-buttons li a')
    _diff_locator = (By.CSS_SELECTOR, '.diff')
    _diff_rows_locator = (By.CSS_SELECTOR, '.diff tbody tr')


class MacroDashboardPage(BasePage):
    """The macro dashboard with names, source links, and usage counts."""
    URL_TEMPLATE = '/{locale}/dashboards/macros'
    TITLE = "Active macros | MDN"

    _table_locator = (By.CSS_SELECTOR, "table.macros-table")
    _count_headers_locator = (By.CSS_SELECTOR, "th.stat-header")
    _source_link_locator = (By.CSS_SELECTOR, "tbody tr th a")
    _search_link_locator = (By.CSS_SELECTOR, "tbody tr td.data a")
    _search_name_input_locator = (By.ID, 'macro-search-name')
    _search_all_btn_locator = (By.ID, 'macro-search-all')
    _search_en_btn_locator = (By.ID, 'macro-search-en')

    @property
    def has_table(self):
        return len(self.find_elements(*self._table_locator)) == 1

    @property
    def has_usage_counts(self):
        count = len(self.find_elements(*self._count_headers_locator))
        assert count in (0, 2)
        return count == 2

    @property
    def first_source_link(self):
        return self.find_element(*self._source_link_locator)

    def click_first_en_search(self):
        en_link = self.find_element(*self._search_link_locator)
        en_link.click()
        self.wait.until(lambda selenium: selenium.title != self.TITLE)

    def click_first_all_search(self):
        all_link = self.find_elements(*self._search_link_locator)[1]
        all_link.click()
        self.wait.until(lambda selenium: selenium.title != self.TITLE)

    def manual_search(self, macro_name, locale='*'):
        name_input = self.find_element(*self._search_name_input_locator)
        name_input.send_keys(macro_name)

        assert locale in ('*', 'en-US')
        if locale == '*':
            btn = self.find_element(*self._search_all_btn_locator)
        else:
            btn = self.find_element(*self._search_en_btn_locator)
        btn.click()
        self.wait.until(lambda selenium: selenium.title != self.TITLE)
