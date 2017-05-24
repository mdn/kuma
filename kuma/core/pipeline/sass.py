from os.path import dirname
from tempfile import NamedTemporaryFile

from django.conf import settings
from pipeline.compilers.sass import SASSCompiler


class DebugSassCompiler(SASSCompiler):
    """
    DEBUG=True replacement for standard SASSCompiler. Same behavior as
    SASSCompiler (e.g. file extension match), but no compilation takes place
    (handled by gulp).
    """

    def compile_file(self, *args, **kwargs):
        return


class SassThenPostCssCompiler(SASSCompiler):
    """Run Sass then PostCSS on the file."""

    def compile_file(self, infile, outfile, outdated=False, force=False):
        with NamedTemporaryFile(suffix='.css') as middlefile:
            middle_path = middlefile.name
            super(SassThenPostCssCompiler, self).compile_file(
                infile, middle_path, outdated, force)

            command = (
                settings.PIPELINE['POSTCSS_BINARY'],
                settings.PIPELINE['POSTCSS_ARGUMENTS'].split(' '),
                middle_path,
                '-o', outfile)
            return self.execute_command(command, cwd=dirname(outfile))
