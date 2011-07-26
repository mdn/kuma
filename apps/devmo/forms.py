from django import forms
from django.conf import settings
from django.contrib.auth import authenticate, forms as auth_forms
from django.contrib.auth.models import User

from tower import ugettext_lazy as _

from devmo.models import UserProfile


class UserProfileEditForm(forms.ModelForm):

    class Meta:
        model = UserProfile
        fields = ('fullname', 'title', 'organization', 'location', 'bio',
                  'interests')

    email = forms.EmailField(label=_('Email'), required=True)
