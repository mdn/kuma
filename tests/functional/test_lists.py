import pytest

from pages.article import ArticlePage
from selenium.webdriver.common.by import By


@pytest.mark.nondestructive
def test_list_macros(base_url, selenium):
    """/en-US/docs/macros returns the macros list."""
    page = ArticlePage(selenium, base_url, locale='en-US',
                       slug='macros').open()
    assert selenium.title == "Active macros | MDN"
    assert len(page.find_elements(By.CSS_SELECTOR, "table.macros-table")) == 1
    # 2 = ElasticSearch is available and populated, 0 = not
    assert len(page.find_elements(By.CSS_SELECTOR, "th.stat-header")) in (0, 2)
