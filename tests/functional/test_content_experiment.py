import pytest

from pages.admin import AdminLogin
from pages.article import ArticlePage
from pages.content_experiment import VariantPage

# Currently no enabled experiments
# TODO: Investigate importing from /kuma/settings/content_experiments.json
CONTENT_EXPERIMENTS = [
    {
        "id": "experiment-interactive-editor",
        "ga_name": "interactive-editor",
        "param": "v",
        "pages": {
            "en-US:Web/JavaScript/Reference/Global_Objects/Array/push": {
                "a": "Web/JavaScript/Reference/Global_Objects/Array/push",
                "b": "Experiment:InteractiveEditor/Array.prototype.push()"
            },
            "en-US:Web/JavaScript/Reference/Global_Objects/Array/concat": {
                "a": "Web/JavaScript/Reference/Global_Objects/Array/concat",
                "b": "Experiment:InteractiveEditor/Array.prototype.concat()"
            },
            "en-US:Web/JavaScript/Reference/Global_Objects/Array/Reduce": {
                "a": "Web/JavaScript/Reference/Global_Objects/Array/Reduce",
                "b": "Experiment:InteractiveEditor/Array.prototype.reduce()"
            },
            "en-US:Web/CSS/transform": {
                "a": "Web/CSS/transform",
                "b": "Experiment:InteractiveEditor/transform"
            },
            "en-US:Web/CSS/box-shadow": {
                "a": "Web/CSS/box-shadow",
                "b": "Experiment:InteractiveEditor/box-shadow"
            },
            "en-US:Web/CSS/background-color": {
                "a": "Web/CSS/background-color",
                "b": "Experiment:InteractiveEditor/background-color"
            }
        }
    }
]

EXPECTED_TITLES = {
    "en-US:Web/JavaScript/Reference/Global_Objects/Array/push":
        "Array.prototype.push() - JavaScript | MDN",
    "en-US:Web/JavaScript/Reference/Global_Objects/Array/concat":
        "Array.prototype.concat() - JavaScript | MDN",
    "en-US:Web/JavaScript/Reference/Global_Objects/Array/Reduce":
        "Array.prototype.reduce() - JavaScript | MDN",
    "en-US:Web/CSS/transform":
        "transform - CSS | MDN",
    "en-US:Web/CSS/box-shadow":
        "box-shadow - CSS | MDN",
    "en-US:Web/CSS/background-color":
        "background-color - CSS | MDN",
}

# Create nicer parameter lists for tests, verbose output
CONTENT_PAGES, CONTENT_VARIANTS = [], []
for exp in CONTENT_EXPERIMENTS:
    for page, variants in exp['pages'].items():
        locale, slug = page.split(':', 1)
        CONTENT_PAGES.append((exp['id'], locale, slug))
        for key in variants.keys():
            CONTENT_VARIANTS.append((exp['id'], locale, slug, key))


def get_experiment_data(exp_id, locale, slug):
    for exp in CONTENT_EXPERIMENTS:
        if exp['id'] == exp_id:
            for page, variants in exp['pages'].items():
                page_locale, page_slug = page.split(':', 1)
                if page_locale == locale and page_slug == slug:
                    return {
                        'ga_name': exp['ga_name'],
                        'param': exp['param'],
                        'expected_title': EXPECTED_TITLES[page],
                        'variants': list(variants.keys())
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
    if page.has_google_analytics:
        assert page.ga_value('siteSpeedSampleRate') == 1


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
        if exp_id == 'experiment-interactive-editor':
            assert page.ga_value('siteSpeedSampleRate') == 100
        else:
            assert page.ga_value('siteSpeedSampleRate') == 1
