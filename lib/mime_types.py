# Mime types used on MDN
MIME_TYPES = {
    'image/gif': '.gif',
    'image/jpeg': '.jpeg, .jpg, .jpe',
    'image/png': '.png',
    'image/svg+xml': '.svg',
    'text/html': '.xml',
    'image/vnd.adobe.photoshop': '.psd',
}

def guess_extension(mime_type):
  if mime_type in MIME_TYPES:
    return MIME_TYPES[mime_type]
  else:
    return None
