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


class NewThreadForm(forms.ModelForm):
    """Form to start a new thread."""

    class Meta:
        model = Thread
        widgets = {
            'forum': forms.HiddenInput,
        }
        exclude = ('created', 'last_post',)
