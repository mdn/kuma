import requests
from celery import task

BASKET_SUBSCRIPTION_URL = 'https://basket.mozilla.org/news/subscribe/'


@task
def subscribe(user):
    logger = subscribe.get_logger()
    data = {
        'newsletters': 'app-dev',
        'format': 'H',
        'email': user.email,
        'lang': user.locale,
        'first_name': user.username
    }
    requests.post(BASKET_SUBSCRIPTION_URL, data=data)
    logger.info(f'Successfully subscribed user {user.email} to newsletter')
