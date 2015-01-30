from django.conf import settings
from django.db import connection, transaction
from django.contrib.contenttypes.models import ContentType

from celery.task import task

# TODO: Figure out a way to do this per-class? Would need to break up some of the SQL calls.
ACTIONCOUNTERS_ANON_GC_WINDOW = getattr(settings, "ACTIONCOUNTERS_ANON_GC_WINDOW", "2 MONTH")
ACTIONCOUNTERS_RECENT_COUNT_WINDOW = getattr(settings, "ACTIONCOUNTERS_RECENT_COUNT_WINDOW", "14 DAY")


@task
def update_actioncounter_counts():
    """Updates the recent and total count columns for action counter fields.
    NOTE: MySQL only and probably a little stupid. FIXME?"""

    # TODO: Make this more robust? Log errors if/when content type or object not found?
    # TODO: Is there a more MySQL-y way to do all of these updates?

    # Accumulate all DB updates here, execute later to minimize DB hits.
    updates = {}

    # Grab a model object by content type and object primary keys
    def get_update(ct_pk, obj_pk):
        key = (ct_pk, obj_pk)
        if key not in updates:
            updates[key] = dict()
        return updates[key]

    cursor = connection.cursor()

    # Garbage collect any counters for anonymous users over a certain age.
    cursor.execute("""
        DELETE
        FROM actioncounters_actioncounterunique
        WHERE
            user_id IS NULL AND
            modified < date_sub(now(), INTERVAL %(interval)s)
    """ % dict(
        interval=ACTIONCOUNTERS_ANON_GC_WINDOW
    ))

    # Any counters too old for the window should be set to 0
    cursor.execute("""
        SELECT content_type_id, object_pk, name
        FROM actioncounters_actioncounterunique
        WHERE modified < date_sub(now(), INTERVAL %(interval)s)
        GROUP BY content_type_id, object_pk, name
    """ % dict(
        interval=ACTIONCOUNTERS_RECENT_COUNT_WINDOW
    ))
    for row in cursor.fetchall():
        get_update(row[0], row[1])['%s_recent' % row[2]] = 0

    # Sum up the counters within the history window.
    cursor.execute("""
        SELECT content_type_id, object_pk, name, sum(total) AS recent_total
        FROM actioncounters_actioncounterunique
        WHERE modified >= date_sub(now(), INTERVAL %(interval)s)
        GROUP BY content_type_id, object_pk, name
    """ % dict(
        interval=ACTIONCOUNTERS_RECENT_COUNT_WINDOW
    ))
    for row in cursor.fetchall():
        get_update(row[0], row[1])['%s_recent' % row[2]] = row[3]

    # Update the action count totals for all objects, for good measure
    cursor.execute("""
        SELECT content_type_id, object_pk, name, sum(total) AS total
        FROM actioncounters_actioncounterunique
        GROUP BY content_type_id, object_pk, name
    """)
    for row in cursor.fetchall():
        get_update(row[0], row[1])['%s_total' % row[2]] = row[3]

    # Finally, perform all the counter updates within a transaction...
    @transaction.atomic
    def perform_updates():
        for key, update in updates.items():
            (ct_pk, obj_pk) = key
            # FYI, get_for_id is cached by ContentType
            ct = ContentType.objects.get_for_id(ct_pk)
            model_class = ct.model_class()
            # Results in a specific UPDATE statement without a full save()
            model_class.objects.filter(pk=obj_pk).update(**update)

    perform_updates()
