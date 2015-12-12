from django.conf import settings
from pipeline.compressors import SubProcessCompressor

cleancss = getattr(settings, 'PIPELINE_CLEANCSS_BINARY', 'cleancss')


class CleanCSSCompressor(SubProcessCompressor):
    def compress_css(self, css):
        return self.execute_command(cleancss, css)
