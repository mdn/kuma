import os
import hashlib
import six

from django.conf import settings
from django.contrib.staticfiles.storage import staticfiles_storage
from django.utils import crypto
from django.utils.functional import cached_property
from django.utils.safestring import mark_safe

from cacheback.base import Job, to_bytestring
from statici18n.utils import get_filename


class KumaJob(Job):
    """
    A subclass of the cache base job class that implements an optional per job
    version key.
    """
    version = None

    def key(self, *args, **kwargs):
        key = super(KumaJob, self).key(*args, **kwargs)
        if self.version is not None:
            key = '%s#%s' % (key, self.version)
        return key

    def hash(self, value):
        """
        Generate a hash of the given tuple.

        This is for use in a cache key.

        A fix till https://github.com/codeinthehole/django-cacheback/pull/40
        is merged and released.
        """
        if isinstance(value, tuple):
            value = tuple(to_bytestring(v) for v in value)
        return hashlib.md5(six.b(':').join(value)).hexdigest()


class GenerationJob(KumaJob):
    generation_age = 60 * 60 * 24 * 365

    def __init__(self, *args, **kwargs):
        self.generation_args = kwargs.pop('generation_args', [])
        super(KumaJob, self).__init__(*args, **kwargs)

    @cached_property
    def generation_key(self):
        generation_args = ':'.join([str(key) for key in self.generation_args])
        return '%s:%s:generation' % (self.class_path, generation_args)

    def key(self, *args, **kwargs):
        key = super(GenerationJob, self).key(*args, **kwargs)
        return '%s@%s' % (key, self.generation())

    def generation(self):
        """
        A random key to be used in cache calls that allows
        invalidating all values created with it. Use it with
        the version parameter of cache.get/set.
        """
        generation = self.cache.get(self.generation_key)
        if generation is None:
            generation = self.renew()
        return generation

    def renew(self):
        """
        Delete the current generation cache key and by that invalidate all
        generation based cached values. Also create a new generation right
        away.
        """
        generation = crypto.get_random_string(length=12)
        self.cache.set(self.generation_key,
                       generation,
                       self.generation_age)
        return generation


class IPBanJob(KumaJob):
    lifetime = 60 * 60 * 3
    refresh_timeout = 60

    def fetch(self, ip):
        from .models import IPBan
        if IPBan.objects.active(ip=ip).exists():
            return "0/s"
        return "60/m"

    def empty(self):
        return "60/m"


class StaticI18nJob(KumaJob):
    lifetime = 60 * 60 * 24

    def fetch(self, locale):
        if not locale:
            locale = settings.LANGUAGE_CODE
        filename = get_filename(locale, settings.STATICI18N_DOMAIN)
        path = os.path.join(settings.STATICI18N_OUTPUT_DIR, filename)
        with staticfiles_storage.open(path) as i18n_file:
            return mark_safe(i18n_file.read())
