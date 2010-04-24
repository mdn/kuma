from django import forms

from .models import Post

class ReplyForm(forms.ModelForm):
    """Reply form for forum threads."""

    class Meta:
        model = Post
        widgets = {
            'thread': forms.HiddenInput,
            'author': forms.HiddenInput,
        }
