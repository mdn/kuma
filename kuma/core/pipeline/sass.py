from __future__ import unicode_literals

from pipeline.compilers.sass import SASSCompiler


class DebugSassCompiler(SASSCompiler):
    """
    DEBUG=True replacement for standard SASSCompiler. Same behavior as
    SASSCompiler (e.g. file extension match), but no compilation takes place
    (handled by node-sass).
    """

    def compile_file(self, *args, **kwargs):
        return
