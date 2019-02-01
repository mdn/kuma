from __future__ import unicode_literals

from celery.task import task

from .models import HumansTXT


@task
def humans_txt():
    humans = HumansTXT()
    humans.generate_file()
