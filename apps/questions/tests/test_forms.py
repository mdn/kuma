from nose.tools import eq_

from questions.forms import NewQuestionForm
from questions.tests import TestCaseBase


class TestNewQuestionForm(TestCaseBase):
    """Tests for the NewQuestionForm"""

    def setUp(self):
        super(TestNewQuestionForm, self).setUp()

    def test_metadata_keys(self):
        """Test metadata_field_keys property."""
        # Test the default form
        form = NewQuestionForm()
        expected = ['useragent']
        actual = form.metadata_field_keys
        eq_(expected, actual)

        # Test the form with a product
        product = {'key': 'desktop',
                   'name': 'Firefox on desktop',
                   'extra_fields': ['troubleshooting', 'ff_version',
                                    'os', 'plugins'], }
        form = NewQuestionForm(product=product)
        expected = ['useragent', 'troubleshooting', 'ff_version', 'os',
                    'plugins']
        actual = form.metadata_field_keys
        eq_(expected, actual)

        # Test the form with a product and category
        category = {'key': 'd6',
                   'name': 'I have another kind of problem with Firefox',
                   'extra_fields': ['frequency', 'started'], }
        form = NewQuestionForm(product=product, category=category)
        expected = ['useragent', 'frequency', 'started', 'troubleshooting',
                    'ff_version', 'os', 'plugins']
        actual = form.metadata_field_keys
        eq_(expected, actual)

    def test_cleaned_metadata(self):
        """Test the cleaned_metadata property."""
        # Test with no metadata
        data = {'title': 'Lorem', 'content': 'ipsum', 'email': 't@t.com'}
        product = {'key': 'desktop',
                   'name': 'Firefox on desktop',
                   'extra_fields': ['troubleshooting', 'ff_version',
                                    'os', 'plugins'], }
        form = NewQuestionForm(product=product, data=data)
        form.is_valid()
        expected = {}
        actual = form.cleaned_metadata
        eq_(expected, actual)

        # Test with metadata
        data['os'] = u'Linux'
        form = NewQuestionForm(product=product, data=data)
        form.is_valid()
        expected = {'os': u'Linux'}
        actual = form.cleaned_metadata
        eq_(expected, actual)

        # Add an empty metadata value
        data['ff_version'] = u''
        form = NewQuestionForm(product=product, data=data)
        form.is_valid()
        expected = {'os': u'Linux'}
        actual = form.cleaned_metadata
        eq_(expected, actual)
