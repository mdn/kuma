from django import forms

from tower import ugettext_lazy as _lazy

from .models import Thread, Post


MSG_CONTENT = _lazy('Content must be longer than 5 characters.')
MSG_TITLE = _lazy('Title must be longer than 5 characters.')


# TODO: remove this and use strip kwarg once ticket #6362 is done
# @see http://code.djangoproject.com/ticket/6362
class StrippedCharField(forms.CharField):
    """CharField that strips trailing and leading spaces."""
    def clean(self, value):
        if value is not None:
            value = value.strip()
        return super(StrippedCharField, self).clean(value)


class ReplyForm(forms.ModelForm):
    """Reply form for forum threads."""
    content = StrippedCharField(
                min_length=5,
                max_length=10000,
                widget=forms.Textarea(attrs={'rows': 10, 'cols': 80}),
                error_messages={'required': MSG_CONTENT,
                                'min_length': MSG_CONTENT})

    class Meta:
        model = Post
        exclude = ('thread', 'author', 'updated_by')


class NewThreadForm(forms.Form):
    """Form to start a new thread."""
    title = StrippedCharField(min_length=5, max_length=255,
                              widget=forms.TextInput(attrs={'size': 80}),
                              error_messages={'required': MSG_TITLE,
                                              'min_length': MSG_CONTENT})
    content = StrippedCharField(
                min_length=5,
                max_length=10000,
                widget=forms.Textarea(attrs={'rows': 30, 'cols': 76}),
                error_messages={'required': MSG_CONTENT,
                                'min_length': MSG_CONTENT})


class EditThreadForm(forms.ModelForm):
    """Form to start a new thread."""
    title = StrippedCharField(min_length=5, max_length=255,
                              widget=forms.TextInput(attrs={'size': 80}),
                              error_messages={'required': MSG_TITLE})

    class Meta:
        model = Thread
        fields = ('title',)


class EditPostForm(forms.Form):
    """Form to edit an existing post."""
    content = StrippedCharField(
            min_length=5,
            max_length=10000,
            widget=forms.Textarea(attrs={'rows': 30, 'cols': 76}),
            error_messages={'required': MSG_CONTENT,
                            'min_length': MSG_CONTENT})

    class Meta:
        model = Post
        exclude = ('thread', 'author', 'updated_by')
