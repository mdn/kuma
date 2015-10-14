from pipeline.compressors import SubProcessCompressor

class CleanCSSCompressor(SubProcessCompressor):
    def compress_css(self, css):
        return self.execute_command('cleancss', css)
