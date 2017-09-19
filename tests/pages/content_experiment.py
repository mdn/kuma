from selenium.webdriver.common.by import By

from pages.article import ArticlePage


class VariantPage(ArticlePage):
    """A variant page under a content experiment."""

    URL_TEMPLATE = '/{locale}/docs/{slug}?{param}={variant}'
    _canonical_locator = (By.CSS_SELECTOR, 'head link[rel=canonical]')

    def __init__(self, *args, **kwargs):
        """Default path is /en-US/docs/User:anonymous:uitest?v=control"""
        param = kwargs.pop('param', 'v')
        variant = kwargs.pop('variant', None)
        assert variant is not None
        super(VariantPage, self).__init__(param=param, variant=variant,
                                          *args, **kwargs)

    @property
    def canonical_url(self):
        canon_link = self.find_element(*self._canonical_locator)
        return canon_link and canon_link.get_attribute('href')
