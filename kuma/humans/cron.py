import cronjobs

from .models import HumansTXT


@cronjobs.register
def humans_txt():
    humans = HumansTXT()
    humans.generate_file()
