import pytest

from pages.home import HomePage

TEST_LOCALE = 'fr'


@pytest.mark.smoke
@pytest.mark.nondestructive
def test_footer_language_selector(base_url, selenium):
    # open homepge
    page = HomePage(selenium, base_url).open()

    # pick and load locale
    page.footer.select_language(TEST_LOCALE)

    # test locale in URL matches
    assert '/' + TEST_LOCALE + '/' in selenium.current_url, 'locale not in URL'

    # test locale in language selector matches
    home_footer_language = page.footer.language_value
    assert home_footer_language == TEST_LOCALE, 'unexpected homepage footer locale'

    # open feedback link
    feedback = page.header.open_feedback()

    # test locale in feedback url matches
    assert '/' + TEST_LOCALE + '/' in selenium.current_url, 'locale not in URL'

    # test locale in feedback footer matches
    feedback_footer_language = feedback.footer.language_value
    assert feedback_footer_language.startswith('/' + TEST_LOCALE), 'unexpected footer locale'
