import requests
from celery import task

BASKET_SUBSCRIPTION_URL = 'https://basket.mozilla.org/news/subscribe/'


@task
def subscribe(pk, email, username, locale):
    from .models import User
    logger = subscribe.get_logger()
    try:
        data = {
            'newsletters': 'app-dev',
            'format': 'H',
            'email': email,
            'lang': locale,
            'first_name': username
        }
        requests.post(BASKET_SUBSCRIPTION_URL, data=data)
        User.objects.filter(pk=pk).update(salesforce_connection='success')
        logger.info(f'Successfully subscribed user {email} to newsletter')
    except Exception as e:
        User.objects.filter(pk=pk).update(salesforce_connection='error')
        raise e
