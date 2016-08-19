import pytest

from utils.urls import assert_valid_url
from pages.home import HomePage
from pages.article import ArticlePage
from pages.search import SearchPage

SEARCH_TERM = 'css'
SEARCH_TERM_ZERO = 'skwiz'
ARTICLE_PATH = 'docs/User:anonymous:uitest'


@pytest.mark.smoke
@pytest.mark.nondestructive
def test_search_homepage(base_url, selenium):
    # open homepage
    page = HomePage(selenium, base_url).open()
    # search for CSS in big box
    search = page.search_for_term(SEARCH_TERM)
    # search term is in search box
    assert search.search_input_value == SEARCH_TERM, 'search term not preserved'
    # results found
    assert search.search_result_items_length == 10


@pytest.mark.smoke
@pytest.mark.nondestructive
def test_search_home_header(base_url, selenium):
    # open homepage
    page = HomePage(selenium, base_url).open()
    # focus on search in nav menu
    width_before = page.header.search_field_width
    page.header.search_field_focus()
    width_after = page.header.search_field_width
    assert width_before < width_after
    # search for CSS
    search = page.header.search_for_term(SEARCH_TERM)
    # search term is in search box
    assert search.search_input_value == SEARCH_TERM, 'search term not preserved'
    # results found
    assert search.search_result_items_length == 10


@pytest.mark.smoke
@pytest.mark.nondestructive
def test_search_article_header(base_url, selenium):
    # open article page
    page = ArticlePage(selenium, base_url, path=ARTICLE_PATH).open()
    # focus on search in nav menu
    width_before = page.header.search_field_width
    page.header.search_field_focus()
    width_after = page.header.search_field_width
    assert width_before < width_after
    # search for CSS
    search = page.header.search_for_term(SEARCH_TERM)
    # search term is in search box
    assert search.search_input_value == SEARCH_TERM, 'search term not preserved'
    # results found
    assert search.search_result_items_length == 10


@pytest.mark.smoke
@pytest.mark.nondestructive
def test_search_layout(base_url, selenium):
    page = SearchPage(selenium, base_url, term=SEARCH_TERM).open()
    # search term is in search box
    assert page.search_input_value == SEARCH_TERM, 'search term not preserved'
    # results found
    assert page.search_result_items_length == 10
    # verrify layout and formatting
    assert page.is_results_explanation_displayed
    assert page.is_main_column_present
    assert page.is_side_column_present
    assert page.is_article_columns_expected_layout
    # default web topics checked
    assert page.is_css_filter_checked
    assert page.is_html_filter_checked
    assert page.is_javascript_filter_checked
    # 10 results
    assert page.search_result_items_length == 10
    # pagination
    assert page.is_next_button_displayed
    # links work
    search_results_links = page.search_results_link_list
    for link in search_results_links:
        this_link = link.get_attribute('href')
        assert_valid_url(this_link, follow_redirects=True)


@pytest.mark.smoke
@pytest.mark.nondestructive
def test_search_zero_results(base_url, selenium):
    page = SearchPage(selenium, base_url, term=SEARCH_TERM_ZERO).open()
    # results found
    assert page.search_result_items_length == 0


@pytest.mark.smoke
@pytest.mark.nondestructive
def test_search_filters(base_url, selenium):
    page = SearchPage(selenium, base_url, term=SEARCH_TERM).open()
    documents_found_initial = page.documents_found
    page.search_all_topics()
    documents_found_after = page.documents_found
    assert documents_found_after > documents_found_initial, 'all topics filter did not increase results returned'
