from django.core.files import temp as tempfile


def make_test_file(content=None, suffix=".txt"):
    """
    Create a fake file for testing purposes.
    """
    if content is None:
        content = "I am a test file for upload."
    # Shamelessly stolen from Django's own file-upload tests.
    tdir = tempfile.gettempdir()
    file_for_upload = tempfile.NamedTemporaryFile(suffix=suffix, dir=tdir)
    file_for_upload.write(content.encode())
    file_for_upload.seek(0)
    return file_for_upload
