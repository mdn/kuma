# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from django.core.exceptions import ValidationError
from django.utils import translation

from nose.tools import eq_

from sumo.form_fields import _format_decimal, TypedMultipleChoiceField
from sumo.tests import TestCase


class TestFormatDecimal(TestCase):

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


class TypedMultipleChoiceFieldTestCase(TestCase):
    """TypedMultipleChoiceField is just like MultipleChoiceField
    except, instead of validating, it coerces types."""

    def assertRaisesErrorWithMessage(self, error, message, callable, *args,
                                     **kwargs):
        self.assertRaises(error, callable, *args, **kwargs)
        try:
            callable(*args, **kwargs)
        except error, e:
            eq_(message, str(e))

    def test_typedmultiplechoicefield_71(self):
        f = TypedMultipleChoiceField(choices=[(1, "+1"), (-1, "-1")],
                                     coerce=int)
        eq_([1], f.clean(['1']))
        self.assertRaisesErrorWithMessage(
            ValidationError,
            "[u'Select a valid choice. 2 is not one of the available choices."
            "']", f.clean, ['2'])

    def test_typedmultiplechoicefield_72(self):
        # Different coercion, same validation.
        f = TypedMultipleChoiceField(choices=[(1, "+1"), (-1, "-1")],
                                     coerce=float)
        eq_([1.0], f.clean(['1']))

    def test_typedmultiplechoicefield_73(self):
        # This can also cause weirdness: bool(-1) == True
        f = TypedMultipleChoiceField(choices=[(1, "+1"), (-1, "-1")],
                                     coerce=bool)
        eq_([True], f.clean(['-1']))

    def test_typedmultiplechoicefield_74(self):
        # Even more weirdness: if you have a valid choice but your coercion
        # function can't coerce, you'll still get a validation error.
        # Don't do this!
        f = TypedMultipleChoiceField(choices=[('A', 'A'), ('B', 'B')],
                                     coerce=int)
        self.assertRaisesErrorWithMessage(
            ValidationError,
            "[u'Select a valid choice. B is not one of the available choices."
            "']", f.clean, ['B'])
        # Required fields require values
        self.assertRaisesErrorWithMessage(
            ValidationError, "[u'This field is required.']", f.clean, [])

    def test_typedmultiplechoicefield_75(self):
        # Non-required fields aren't required
        f = TypedMultipleChoiceField(choices=[(1, "+1"), (-1, "-1")],
                                     coerce=int, required=False)
        eq_([], f.clean([]))

    def test_typedmultiplechoicefield_76(self):
        # If you want cleaning an empty value to return a different type,
        # tell the field
        f = TypedMultipleChoiceField(choices=[(1, "+1"), (-1, "-1")],
                                     coerce=int, required=False,
                                     empty_value=None)
        eq_(None, f.clean([]))

    def test_coerce_only(self):
        """No validation error raised in this case."""
        f = TypedMultipleChoiceField(choices=[(1, '+1')], coerce=int,
                                     coerce_only=True)
        eq_([], f.clean(['2']))
