from celery.task import task
from tower import ugettext_lazy as _

from django.conf import settings
from django.contrib.auth.models import User
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string


@task
def send_welcome_email(user_pk):
    user = User.objects.get(pk=user_pk)

    context = {'username': user.username}
    content_plain = render_to_string('users/email/welcome/plain.ltxt', context)
    content_html = render_to_string('users/email/welcome/html.ltxt', context)

    email = EmailMultiAlternatives(
        _('Take the next step to get involved on MDN!'),
        content_plain,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
    )
    email.attach_alternative(content_html, 'text/html')
    email.send()
