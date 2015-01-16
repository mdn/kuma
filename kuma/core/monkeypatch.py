from django.forms import fields, widgets

# Monkey patch preserves the old values, so we can pick up any changes
# in CharField.widget_attrs and Field.widget_attrs
# paulc filed a Django ticket for it, #14884
field_widget_attrs = fields.Field.widget_attrs
charfield_widget_attrs = fields.CharField.widget_attrs


def required_field_attrs(self, widget):
    """This function is for use on the base Field class."""
    attrs = field_widget_attrs(self, widget)
    if self.required and 'required' not in attrs:
        attrs['required'] = 'required'
    return attrs


def required_char_field_attrs(self, widget, *args, **kwargs):
    """This function is for use on the CharField class."""
    # We need to call super() here, since Django's CharField.widget_attrs
    # doesn't call its super and thus won't use the required_field_attrs above.
    attrs = super(fields.CharField, self).widget_attrs(widget, *args, **kwargs)
    original_attrs = charfield_widget_attrs(self, widget) or {}
    attrs.update(original_attrs)
    return attrs


def render_file_not_required_with_value(self, name, value, attrs=None):
    # If the file field has a value, then ensure the empty widget is not marked
    # as required for HTML5 form validation.
    if value and 'required' in self.attrs:
        del self.attrs['required']
    return super(widgets.FileInput, self).render(name, None, attrs=attrs)


class DateWidget(fields.DateField.widget):
    input_type = 'date'


class TimeWidget(fields.TimeField.widget):
    input_type = 'time'


class URLWidget(fields.URLField.widget):
    input_type = 'url'


class EmailWidget(fields.EmailField.widget):
    input_type = 'email'


fields.Field.widget_attrs = required_field_attrs
fields.CharField.widget_attrs = required_char_field_attrs
fields.DateField.widget = DateWidget
fields.TimeField.widget = TimeWidget
fields.URLField.widget = URLWidget
fields.EmailField.widget = EmailWidget

widgets.FileInput.render = render_file_not_required_with_value
