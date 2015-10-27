from django.contrib.staticfiles.storage import ManifestStaticFilesStorage
from pipeline.storage import PipelineMixin


class PipelineManifestStorage(PipelineMixin, ManifestStaticFilesStorage):
    pass
