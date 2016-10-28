import pytest
from utils.urls import assert_valid_url
from pages.article import ArticlePage

ARTICLE_NAME = 'Send feedback on MDN'
ARTICLE_TITLE_SUFIX = " - The MDN project | MDN"
ARTICLE_PATH = 'docs/MDN/Feedback'


@pytest.mark.smoke
@pytest.mark.nondestructive
def test_location(base_url, selenium):
    article_page = ArticlePage(selenium, base_url, path=ARTICLE_PATH).open()
    page = article_page.header.open_feedback('en-US', path=ARTICLE_PATH)
    assert page.seed_url in selenium.current_url
    assert (ARTICLE_NAME + ARTICLE_TITLE_SUFIX) == selenium.title, 'page title does not match expected'
    assert page.article_title_text == ARTICLE_NAME, 'article title is not expected'
    assert page.article_title_text in selenium.title, 'article title not in page title'


@pytest.mark.smoke
@pytest.mark.nondestructive
def test_feedback_layout(base_url, selenium):
    page = ArticlePage(selenium, base_url, path=ARTICLE_PATH).open()
    assert page.is_article_displayed
    assert page.is_article_column_left_present
    assert page.is_article_column_content_present
    assert page.article_column_right_present
    assert page.is_article_columns_expected_layout


@pytest.mark.smoke
@pytest.mark.nondestructive
def test_page_links(base_url, selenium):
    page = ArticlePage(selenium, base_url, path=ARTICLE_PATH).open()
    # get all page links
    article_links = page.article_link_list
    for link in article_links:
        this_link = link.get_attribute('href')
        # exclude IRC, we can't handle that protocol
        if not this_link.startswith('irc'):
            assert_valid_url(this_link, follow_redirects=True)
