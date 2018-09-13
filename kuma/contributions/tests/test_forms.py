from kuma.contributions.forms import ContributionForm, DONATION_CHOICES
from kuma.core.tests import KumaTestCase


class TestContributionForm(KumaTestCase):

    def test_form_validation(self):

        def _is_valid_false(self, type_to_check=False):
            form = ContributionForm(data)
            self.assertEqual(form.is_valid(), type_to_check)

        data = {
            'name': 'test name'
        }
        _is_valid_false(self)

        data['email'] = 'some-bad-email@tett'
        _is_valid_false(self)

        data['email'] = 'some-good-email@test.com'
        _is_valid_false(self)

        data['donation_choices'] = 'string'
        _is_valid_false(self)

        data['donation_choices'] = DONATION_CHOICES[1][0]
        data['donation_amount'] = 12
        _is_valid_false(self)

        del data['donation_amount']
        _is_valid_false(self, True)
