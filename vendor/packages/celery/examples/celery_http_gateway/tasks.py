from celery.task import task


@task
def hello_world(to="world"):
    return "Hello %s" % to
