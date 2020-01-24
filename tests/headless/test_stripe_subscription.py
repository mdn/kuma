import pytest
import requests

from django.urls import reverse

from kuma.core.utils import safer_pyquery as pq


@pytest.mark.headless
def test_create_stripe_subscription(site_url):
    response = requests.post(
        'http://' + site_url + reverse('users.create_stripe_subscription') + '?test_mode=True',
        {
            'stripe_token': 'tok_visa',
            'stripe_email': 'payer@example.com'
        },
        allow_redirects=True
    )
    page = pq(response.content)
    assert 'Visa ending in 4242' in page('.card-info p').text()
