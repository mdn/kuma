import mimetypes

# Mime types used on MDN
MIME_TYPES = {
    'image/jpeg': '.jpeg, .jpg, .jpe',
    'image/vnd.adobe.photoshop': '.psd',
}

def guess_extension(mime_type):
  if mime_type in MIME_TYPES:
    return MIME_TYPES[mime_type]
  else:
    return mimetypes.guess_extension(mime_type)
