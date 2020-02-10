from django.conf import settings
from pipeline.compressors import SubProcessCompressor


class CleanCSSCompressor(SubProcessCompressor):
    def compress_css(self, css):
        binary = settings.PIPELINE.get("CLEANCSS_BINARY", "cleancss")
        args = settings.PIPELINE.get("CLEANCSS_ARGUMENTS", "")
        # If the arguments ever include quoted arguments with spaces then
        # the simple split() call here is not going to be good enough.
        command = (binary,) + tuple(args.split())
        return self.execute_command(command, css)
