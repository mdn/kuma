from celery.task import task

from .models import HumansTXT


@task
def humans_txt():
    humans = HumansTXT()
    humans.generate_file()
