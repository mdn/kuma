

from django.utils import translation

from . import KumaTestCase
from ..form_fields import _format_decimal


class TestFormatDecimal(KumaTestCase):

    def test_default_locale(self):
        """Default locale just works"""
        num = _format_decimal(1234.567)
        assert '1,234.567' == num

    def test_fr_locale(self):
        """French locale returns french format"""
        translation.activate('fr')
        num = _format_decimal(1234.567)
        assert '1\u202f234,567' == num

    def test_xx_YY_locale(self):
        """Falls back to English for unknown Django locales"""
        translation.activate('xx-YY')
        # Note: this activation does not make Django attempt to use xx-YY
        assert 'xx-yy' == translation.get_language()
        num = _format_decimal(1234.567)
        assert '1,234.567' == num

    def test_pt_BR_locale(self):
        """Falls back to English for unknown babel locales"""
        # Note: if this starts to fail for no apparent reason, it's probably
        # because babel learned about pt-BR since this test was written.
        translation.activate('pt-BR')
        assert 'pt-br' == translation.get_language()
        num = _format_decimal(1234.567)
        assert '1,234.567' == num
