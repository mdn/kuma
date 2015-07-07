from kuma.core.jobs import KumaJob


class DocumentZoneStackJob(KumaJob):
    lifetime = 60 * 60 * 3
    refresh_timeout = 60

    def fetch(self, pk):
        """
        Assemble the stack of DocumentZones available from this document,
        moving up the stack of topic parents
        """
        from .models import Document, DocumentZone
        document = Document.objects.get(pk=pk)
        stack = []
        try:
            stack.append(DocumentZone.objects.get(document=document))
        except DocumentZone.DoesNotExist:
            pass
        for parent in document.get_topic_parents():
            try:
                stack.append(DocumentZone.objects.get(document=parent))
            except DocumentZone.DoesNotExist:
                pass
        return stack

    def empty(self):
        return []


class DocumentZoneURLRemapsJob(KumaJob):
    lifetime = 60 * 60 * 3
    refresh_timeout = 60

    def fetch(self, locale):
        from .models import DocumentZone
        zones = (DocumentZone.objects.filter(document__locale=locale,
                                             url_root__isnull=False)
                                     .exclude(url_root=''))
        remaps = [('/docs/%s' % zone.document.slug, '/%s' % zone.url_root)
                  for zone in zones]
        return remaps

    def empty(self):
        # the empty result needs to be an empty list instead of None
        return []
