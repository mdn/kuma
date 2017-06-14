import pytest

from pages.admin import AdminLogin
from pages.article import ArticlePage
from pages.content_experiment import VariantPage

# Currently no enabled experiments
# TODO: Investigate importing from /kuma/settings/content_experiments.json
CONTENT_EXPERIMENTS = []
EXPECTED_TITLES = {}

# Create nicer parameter lists for tests, verbose output
CONTENT_PAGES, CONTENT_VARIANTS = [], []
for exp in CONTENT_EXPERIMENTS:
    for page in exp['pages']:
        CONTENT_PAGES.append((exp['id'], page['locale'], page['slug']))
        for variant in page['variants']:
            CONTENT_VARIANTS.append((exp['id'], page['locale'], page['slug'],
                                     variant[0]))


def get_experiment_data(exp_id, locale, slug):
    for exp in CONTENT_EXPERIMENTS:
        if exp['id'] == exp_id:
            for page in exp['pages']:
                if page['locale'] == locale and page['slug'] == slug:
                    return {
                        'ga_name': exp['ga_name'],
                        'param': exp['param'],
                        'expected_title': EXPECTED_TITLES[(locale, slug)],
                        'variants': [name for name, src in page['variants']],
                    }
    raise Exception("Invalid experiment")


@pytest.mark.nondestructive
@pytest.mark.parametrize("exp_id,locale,slug", CONTENT_PAGES)
def test_content_exp_redirect(base_url, selenium, exp_id, locale, slug):
    data = get_experiment_data(exp_id, locale, slug)
    page = ArticlePage(selenium, base_url, locale=locale, slug=slug).open()
    assert selenium.title == data['expected_title']
    seed_url = page.seed_url
    expected_variant_urls = ["%s?%s=%s" % (seed_url, data['param'], variant)
                             for variant in data['variants']]
    assert selenium.current_url in expected_variant_urls
    assert not page.has_edit_button


@pytest.mark.login
@pytest.mark.nondestructive
@pytest.mark.parametrize("exp_id,locale,slug", CONTENT_PAGES)
def test_content_exp_logged_in(base_url, selenium, exp_id, locale, slug):
    data = get_experiment_data(exp_id, locale, slug)
    admin = AdminLogin(selenium, base_url).open()
    admin.login_new_user()
    page = ArticlePage(selenium, base_url, locale=locale, slug=slug).open()
    assert selenium.title == data['expected_title']
    assert selenium.current_url == page.seed_url
    assert page.has_edit_button


@pytest.mark.nondestructive
@pytest.mark.parametrize("exp_id,locale,slug,variant", CONTENT_VARIANTS)
def test_content_exp_variant(
        base_url, selenium, exp_id, locale, slug, variant):
    data = get_experiment_data(exp_id, locale, slug)
    page = VariantPage(selenium, base_url, locale=locale, slug=slug,
                       param=data['param'], variant=variant).open()
    assert selenium.current_url == page.seed_url
    assert selenium.title == data['expected_title']
    expected_canonical = page.seed_url.split('?')[0]
    assert page.canonical_url == expected_canonical
    assert not page.has_edit_button
    if page.has_google_analytics:
        expected_dim15 = "%s:%s" % (data['ga_name'], variant)
        assert page.ga_value('dimension15') == expected_dim15
        assert page.ga_value('dimension16') == "/%s/docs/%s" % (locale, slug)
