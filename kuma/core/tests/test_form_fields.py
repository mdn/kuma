from django.utils import translation

from nose.tools import eq_

from kuma.core.tests import KumaTestCase

from ..form_fields import _format_decimal


class TestFormatDecimal(KumaTestCase):

    def test_default_locale(self):
        """Default locale just works"""
        num = _format_decimal(1234.567)
        eq_('1,234.567', num)

    def test_fr_locale(self):
        """French locale returns french format"""
        translation.activate('fr')
        num = _format_decimal(1234.567)
        eq_(u'1\xa0234,567', num)

    def test_xx_YY_locale(self):
        """Falls back to English for unknown Django locales"""
        translation.activate('xx-YY')
        # Note: this activation does not make Django attempt to use xx-YY
        eq_('en-us', translation.get_language())
        num = _format_decimal(1234.567)
        eq_('1,234.567', num)

    def test_fy_NL_locale(self):
        """Falls back to English for unknown babel locales"""
        # Note: if this starts to fail for no apparent reason, it's probably
        # because babel learned about fy-NL since this test was written.
        translation.activate('fy-NL')
        eq_('fy-nl', translation.get_language())
        num = _format_decimal(1234.567)
        eq_('1,234.567', num)
