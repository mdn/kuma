import requests
from celery import task

BASKET_SUBSCRIPTION_URL = 'https://basket.mozilla.org/news/subscribe/'


@task
def subscribe(pk, email, username, locale):
    # We need to import User here as Python can't resolve circular dependencies otherwise
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
        # TODO: Use request_retry_session() once #5424 lands
        response = requests.post(BASKET_SUBSCRIPTION_URL, data=data)
        response.raise_for_status()
        User.objects.filter(pk=pk).update(salesforce_connection='success')
        logger.info(f'Successfully subscribed user {email} to newsletter')
    except Exception:
        User.objects.filter(pk=pk).update(salesforce_connection='error')
        raise
