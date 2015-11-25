from jingo import register

from .utils import allow_add_attachment_by, attachments_payload

register.function(allow_add_attachment_by)

register.function(attachments_payload)
