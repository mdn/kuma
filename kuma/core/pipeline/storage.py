from django.conf import settings
from django.contrib.staticfiles.storage import ManifestStaticFilesStorage

from pipeline.storage import PipelineMixin


class ManifestPipelineStorage(PipelineMixin, ManifestStaticFilesStorage):
    packing = not settings.DEBUG
