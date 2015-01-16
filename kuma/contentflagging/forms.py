from django import forms

from django.conf import settings

from .models import ContentFlag


class ContentFlagForm(forms.ModelForm):
    """Form for accepting a content moderation flag submission"""
    class Meta:
        model = ContentFlag
        fields = ('flag_type', 'explanation')

    flag_type = forms.ChoiceField(choices=settings.DEMO_FLAG_REASONS,
                                  widget=forms.RadioSelect)

    def clean(self):
        cleaned_data = super(ContentFlagForm, self).clean()
        return cleaned_data

    def as_ul(self):
        "Returns this form rendered as HTML <li>s -- excluding the <ul></ul>."
        return self._html_output(
            normal_row=u'<li%(html_class_attr)s>%(label)s %(field)s%(help_text)s%(errors)s</li>',
            error_row=u'<li>%s</li>',
            row_ender='</li>',
            help_text_html=u' <p class="help">%s</p>',
            errors_on_separate_row=False)
