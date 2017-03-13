import pytest
from selenium.webdriver.common.by import By

from pages.base import BasePage


@pytest.mark.nondestructive
@pytest.mark.maintenance_mode
def test_revision_in_mm(base_url, selenium):
    # Get the link for the first (could be any) revision of the test document.
    page = BasePage(selenium, base_url)
    page.URL_TEMPLATE = '/{locale}/docs/User:anonymous:uitest$history'
    page.open()
    rev_link = page.find_element(
        By.CSS_SELECTOR,
        ('div.revision-list-contain ul.revision-list '
         'li:first-child div.revision-list-date a')
    )
    # Check that we're not displaying the "REVERT TO THIS REVISION" button.
    page.URL_TEMPLATE = rev_link.get_attribute('href')
    page.open()
    assert not page.is_element_displayed(
        By.CSS_SELECTOR, 'article > a.button.revert-revision')
    assert page.is_maintenance_mode_banner_displayed
    assert not page.header.is_signin_displayed


@pytest.mark.nondestructive
@pytest.mark.maintenance_mode
def test_compare_revisions_in_mm(base_url, selenium):
    # Load the page that compares two revisions of a document.
    page = BasePage(selenium, base_url)
    page.URL_TEMPLATE = '/{locale}/docs/Web/CSS$history'
    page.open()
    compare_button = page.find_element(
        By.CSS_SELECTOR,
        ('div.revision-list-contain > form > '
         'div.revision-list-controls > input.link-btn')
    )
    compare_button.click()
    # Check that we're not displaying the "Change Revisions" link.
    page = BasePage(selenium, base_url)
    page.URL_TEMPLATE = '/{locale}/docs/Web/CSS$compare'
    page.wait_for_page_to_load()
    assert not page.is_element_displayed(
        By.CSS_SELECTOR, '#compare-revisions a.change-revisions')
    assert page.is_maintenance_mode_banner_displayed
    assert not page.header.is_signin_displayed
