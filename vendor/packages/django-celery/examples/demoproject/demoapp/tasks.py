from djcelery import celery


@celery.task
def add(x, y):
    return x + y


@celery.task
def sleeptask(i):
    from time import sleep
    sleep(i)
    return i


@celery.task
def raisetask():
    raise KeyError("foo")
