import pytest
import requests

from pages.notfound import NotFoundPage
from utils.urls import assert_valid_url

ARTICLE_NAME = 'Not Found'
ARTICLE_TITLE_SUFIX = " | MDN"


# page headers
@pytest.mark.smoke
@pytest.mark.nodata
@pytest.mark.nondestructive
@pytest.mark.maintenance_mode
def test_is_not_found_status(base_url, selenium):
    NotFoundPage(selenium, base_url).open()
    assert_valid_url(selenium.current_url, status_code=requests.codes.not_found)


@pytest.mark.nondestructive
@pytest.mark.maintenance_mode
def test_is_not_found_status_in_mm(base_url, selenium):
    page = NotFoundPage(selenium, base_url).open()
    assert page.is_maintenance_mode_banner_displayed
    assert not page.header.is_signin_displayed


@pytest.mark.smoke
@pytest.mark.nodata
@pytest.mark.nondestructive
@pytest.mark.maintenance_mode
def test_is_expected_content(base_url, selenium):
    page = NotFoundPage(selenium, base_url).open()
    assert (ARTICLE_NAME + ARTICLE_TITLE_SUFIX) == selenium.title
    assert page.page_title_text == ARTICLE_NAME
    assert page.page_title_text in selenium.title
    assert page.is_report_link_displayed
