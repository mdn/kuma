import pytest

from pages.home import HomePage


@pytest.mark.smoke
@pytest.mark.nondestructive
@pytest.mark.maintenance_mode
@pytest.mark.parametrize('locale', ['fr'])
def test_footer_language_selector(base_url, selenium, locale):
    # open homepge
    page = HomePage(selenium, base_url).open()

    # pick and load locale
    page.footer.select_language(locale)

    # test locale in URL matches
    assert '/{}/'.format(locale) in selenium.current_url

    # test locale in language selector matches
    assert page.footer.language_value == locale

    # open feedback link
    feedback = page.header.open_feedback(locale=locale)

    # test locale in feedback url matches
    assert '/{}/'.format(locale) in selenium.current_url

    # test locale in feedback footer matches
    assert feedback.footer.language_value.startswith('/' + locale)
