from whitenoise.django import DjangoWhiteNoise


class KumaDjangoWhiteNoise(DjangoWhiteNoise):

    # Custom MIME types
    KUMA_MIMETYPES = (
        ('application/font-woff', '.woff'),
        ('application/font-woff2', '.woff2'),)

    # Use our custom MIME types, together with the default MIME types, in
    # WhiteNoise. When our MIME types conflict with the defaults, use ours.
    EXTRA_MIMETYPES = tuple({e[1]: e for e in reversed(
        KUMA_MIMETYPES + DjangoWhiteNoise.EXTRA_MIMETYPES
    )}.values())
