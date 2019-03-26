from kuma.core.tests import KumaTestCase


class BannerTestMixin(object):
    """Base TestCase for the banners app test cases."""
    fixtures = ['test_banners.json']

    def setUp(self):
        super(BannerTestMixin, self).setUp()


class BannerTestCase(BannerTestMixin, KumaTestCase):
    pass
