from __future__ import absolute_import

from django.db import transaction, connection, models
try:
    from django.db import connections, router
except ImportError:  # pre-Django 1.2
    connections = router = None  # noqa


class QueueManager(models.Manager):

    def publish(self, queue_name, payload):
        queue, created = self.get_or_create(name=queue_name)
        queue.messages.create(payload=payload)

    def fetch(self, queue_name):
        try:
            queue = self.get(name=queue_name)
        except self.model.DoesNotExist:
            return

        return queue.messages.pop()

    def size(self, queue_name):
        return self.get(name=queue_name).messages.count()

    def purge(self, queue_name):
        try:
            queue = self.get(name=queue_name)
        except self.model.DoesNotExist:
            return

        messages = queue.messages.all()
        count = messages.count()
        messages.delete()
        return count


def select_for_update(qs):
    try:
        return qs.select_for_update()
    except AttributeError:
        return qs


class MessageManager(models.Manager):
    _messages_received = [0]
    cleanup_every = 10

    @transaction.commit_manually
    def pop(self):
        try:
            resultset = select_for_update(self.filter(visible=True)
                                            .order_by('sent_at', 'id'))
            result = resultset[0:1].get()
            result.visible = False
            result.save()
            recv = self.__class__._messages_received
            recv[0] += 1
            if not recv[0] % self.cleanup_every:
                self.cleanup()
            transaction.commit()
            return result.payload
        except self.model.DoesNotExist:
            transaction.commit()
        except:
            transaction.rollback()

    def cleanup(self):
        cursor = self.connection_for_write().cursor()
        try:
            cursor.execute("DELETE FROM %s WHERE visible=%%s" % (
                            self.model._meta.db_table, ), (False, ))
        except:
            transaction.rollback_unless_managed()
        else:
            transaction.commit_unless_managed()

    def connection_for_write(self):
        if connections:
            return connections[router.db_for_write(self.model)]
        return connection
