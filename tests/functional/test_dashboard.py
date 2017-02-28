import pytest

from pages.dashboard import DashboardPage
from pages.admin import AdminLogin


@pytest.mark.smoke
@pytest.mark.nondestructive
@pytest.mark.maintenance_mode
def test_dashboard(base_url, selenium):
    page = DashboardPage(selenium, base_url).open()
    first_row = page.first_row
    # ip toggle not present
    assert not page.is_ip_toggle_present
    # ip ban not present
    assert not first_row.is_ip_ban_present
    # spam ham button not present
    assert not first_row.is_spam_ham_button_present
    # no dashboard-details
    assert page.details_items_length is 0
    # click first cell
    page.open_first_details()
    # dashboard-details exist and are visible
    assert page.details_items_length is 1
    assert page.is_first_details_displayed
    # contains a diff
    assert page.is_first_details_diff_displayed
    # does not overflow page
    assert page.dashboard_not_overflowing
    # save id of first revision on page one
    first_row_id = page.first_row_id
    # click on page two link
    page.click_page_two()
    # save id of first revision on page tw0
    new_first_row_id = page.first_row_id
    # check first revison on page one is not on page two
    assert first_row_id is not new_first_row_id


@pytest.mark.maintenance_mode
def test_dashboard_in_mm(base_url, selenium):
    page = DashboardPage(selenium, base_url).open()
    assert page.is_maintenance_mode_banner_displayed
    assert not page.header.is_signin_displayed


@pytest.mark.smoke
@pytest.mark.login
@pytest.mark.nondestructive
def test_dashboard_moderator(base_url, selenium):
    admin = AdminLogin(selenium, base_url).open()
    admin.login_moderator_user()
    page = DashboardPage(selenium, base_url).open()
    first_row = page.first_row
    # ip toggle not present
    assert not page.is_ip_toggle_present
    # ip ban not present
    assert not first_row.is_ip_ban_present
    # spam ham button present
    assert first_row.is_spam_ham_button_present


@pytest.mark.smoke
@pytest.mark.login
@pytest.mark.nondestructive
def test_dashboard_super(base_url, selenium):
    admin = AdminLogin(selenium, base_url).open()
    admin.login_super_user()
    page = DashboardPage(selenium, base_url).open()
    first_row = page.first_row
    # ip toggle present
    assert page.is_ip_toggle_present
    # ip ban present
    assert first_row.is_ip_ban_present
    # spam ham button present
    assert first_row.is_spam_ham_button_present
