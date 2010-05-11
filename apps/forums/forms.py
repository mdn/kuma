from django import forms

from .models import Post, Thread


class ReplyForm(forms.ModelForm):
    """Reply form for forum threads."""

    class Meta:
        model = Post
        widgets = {
            'thread': forms.HiddenInput,
            'author': forms.HiddenInput,
        }


class NewThreadForm(forms.Form):
    """Form to start a new thread."""
    title = forms.CharField(min_length=5, max_length=255)
    content = forms.CharField(widget=forms.Textarea)
