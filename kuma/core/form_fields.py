from django import forms
from django.conf import settings
from django.core import validators
from django.core.exceptions import ValidationError
from django.utils import translation

from babel import Locale, localedata
from babel.support import Format
from tower import ugettext_lazy as _lazy


# TODO: remove this and use strip kwarg once ticket #6362 is done
# @see http://code.djangoproject.com/ticket/6362
class StrippedCharField(forms.CharField):
    """CharField that strips trailing and leading spaces."""
    def __init__(self, max_length=None, min_length=None, *args, **kwargs):
        self.max_length, self.min_length = max_length, min_length
        super(StrippedCharField, self).__init__(max_length, min_length,
                                                *args, **kwargs)

        # Remove the default min and max length validators and add our own
        # that format numbers in the error messages.
        to_remove = []
        for validator in self.validators:
            class_name = validator.__class__.__name__
            if class_name == 'MinLengthValidator' or \
               class_name == 'MaxLengthValidator':
                to_remove.append(validator)
        for validator in to_remove:
            self.validators.remove(validator)

        if min_length is not None:
            self.validators.append(MinLengthValidator(min_length))
        if max_length is not None:
            self.validators.append(MaxLengthValidator(max_length))

    def clean(self, value):
        if value is not None:
            value = value.strip()
        return super(StrippedCharField, self).clean(value)


class BaseValidator(validators.BaseValidator):
    """Override the BaseValidator from django to format numbers."""
    def __call__(self, value):
        cleaned = self.clean(value)
        params = {'limit_value': _format_decimal(self.limit_value),
                  'show_value': _format_decimal(cleaned)}
        if self.compare(cleaned, self.limit_value):
            raise ValidationError(
                self.message % params,
                code=self.code,
                params=params,
            )


class MinLengthValidator(validators.MinLengthValidator, BaseValidator):
    message = _lazy(u'Ensure this value has at least %(limit_value)s '
                    u'characters (it has %(show_value)s).')


class MaxLengthValidator(validators.MaxLengthValidator, BaseValidator):
    message = _lazy(u'Ensure this value has at most %(limit_value)s '
                    u'characters (it has %(show_value)s).')


def _format_decimal(num, format=None):
    """Returns the string of a number formatted for the current language.

    Uses django's translation.get_language() to find the current language from
    the request.
    Falls back to the default language if babel does not support the current.

    """
    lang = translation.get_language()
    if not localedata.exists(lang):
        lang = settings.LANGUAGE_CODE
    locale = Locale(translation.to_locale(lang))
    return Format(locale).decimal(num, format)
