from django.conf import settings
from pipeline.compressors import SubProcessCompressor


class CleanCSSCompressor(SubProcessCompressor):
    def compress_css(self, css):
        binary = settings.PIPELINE.get('CLEANCSS_BINARY', 'cleancss')
        args = settings.PIPELINE.get('CLEANCSS_ARGUMENTS', '')
        command = (binary, args) if args else (binary,)
        return self.execute_command(command, css)
