import re
import pytest
from utils.urls import assert_valid_url
from pages.article import ArticlePage

ARTICLE_NAME = 'Send feedback (about|on) MDN'


@pytest.mark.smoke
@pytest.mark.nondestructive
@pytest.mark.maintenance_mode
def test_location(base_url, selenium):
    article_page = ArticlePage(selenium, base_url).open()
    page = article_page.header.open_feedback()
    assert re.match(ARTICLE_NAME + ' - The MDN project \| MDN', selenium.title)
    assert re.match(ARTICLE_NAME, page.article_title_text)
    assert page.article_title_text in selenium.title


@pytest.mark.smoke
@pytest.mark.nondestructive
@pytest.mark.maintenance_mode
def test_feedback_layout(base_url, selenium):
    page = ArticlePage(selenium, base_url).open()
    assert page.is_article_displayed
    assert page.is_article_column_left_present
    assert page.is_article_column_content_present
    assert page.article_column_right_present
    column_container = page.article_column_container_region
    assert column_container.is_expected_stacking


@pytest.mark.smoke
@pytest.mark.nondestructive
@pytest.mark.maintenance_mode
def test_page_links(base_url, selenium):
    page = ArticlePage(selenium, base_url).open()
    # get all page links
    article_links = page.article_link_list
    for link in article_links:
        this_link = link.get_attribute('href')
        # exclude IRC, we can't handle that protocol
        if not this_link.startswith('irc'):
            assert_valid_url(this_link, follow_redirects=True)
