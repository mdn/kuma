import pytest
from selenium.webdriver.common.by import By

from pages.base import BasePage


@pytest.mark.nondestructive
@pytest.mark.maintenance_mode
def test_user_profile_in_mm(base_url, selenium):
    # Check that the edit button is not displayed for a user profile.
    page = BasePage(selenium, base_url)
    page.URL_TEMPLATE = '/{locale}/profiles/test-moderator'
    page.open()
    assert not page.is_element_displayed(By.ID, 'edit-user')
    assert page.is_maintenance_mode_banner_displayed
    assert not page.header.is_signin_displayed
