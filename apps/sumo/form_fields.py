from django import forms


# TODO: remove this and use strip kwarg once ticket #6362 is done
# @see http://code.djangoproject.com/ticket/6362
class StrippedCharField(forms.CharField):
    """CharField that strips trailing and leading spaces."""
    def clean(self, value):
        if value is not None:
            value = value.strip()
        return super(StrippedCharField, self).clean(value)
