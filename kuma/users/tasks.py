from celery.task import task

from django.conf import settings
from django.contrib.auth.models import User
from django.core.mail import EmailMultiAlternatives
from django.template import loader


@task
def send_welcome_email(user_pk):
    user = User.objects.get(pk=user_pk)

    template_vars = {'username': user.username}
    content_plain = loader.render_to_string(
        'users/email/welcome/plain.ltxt', template_vars)
    content_html = loader.render_to_string(
        'users/email/welcome/html.ltxt', template_vars)

    email = EmailMultiAlternatives(
        'Take the next step to get involved on MDN!',
        content_plain,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
    )
    email.attach_alternative(content_html, 'text/html')
    email.send()
