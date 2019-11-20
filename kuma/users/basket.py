import logging

import requests

BASKET_SUBSCRIPTION_URL = 'https://basket.mozilla.org/news/subscribe/'

logger = logging.getLogger('kuma.basket')


def subscribe(user):
    data = {
        'newsletters': 'app-dev',
        'format': 'H',
        'email': user.email,
        'lang': user.locale,
        'first_name': user.username
    }
    try:
        requests.post(BASKET_SUBSCRIPTION_URL, data=data)
        logger.info('Successfully subscribed user {} to newsletter', user.email)
    except requests.exceptions.RequestException as e:
        logger.error('Error while subscribing user {} to newsletter: {}', user.email, e)
