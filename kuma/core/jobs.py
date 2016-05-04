from cacheback.base import Job
from django.utils import crypto


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


class GenerationJob(KumaJob):
    """
    A cacheback value job that is part of a generation group.

    The purpose is to refresh several cached values when a generation changes.
    """
    generation_lifetime = 60 * 60 * 24 * 365
    lifetime = 60 * 60 * 12

    def __init__(self, generation_args=None, *args, **kwargs):
        """
        Initialize the job and prepare the generation.

        All jobs initialized with the same generation_args list will share the
        same generation, and all cached values will be invalidated when the
        generation is invalidated.
        """
        self.generation_args = generation_args or []
        super(KumaJob, self).__init__(*args, **kwargs)
        self.generation_key = GenerationKeyJob(
            lifetime=self.generation_lifetime, for_class=self.class_path,
            generation_args=self.generation_args)

    def key(self, *args, **kwargs):
        """Create a key that is derived from the generation."""
        base_key = super(GenerationJob, self).key(*args, **kwargs)
        gen_key = self.generation_key.key()
        gen_key_value = self.generation_key.get()
        return '%s@%s:%s' % (base_key, gen_key, gen_key_value)

    def invalidate_generation(self):
        """Invalidate the shared generation."""
        self.generation_key.delete()


class GenerationKeyJob(Job):
    """A generation that is shared by several GenerationJobs."""

    def __init__(self, lifetime, for_class, generation_args, *args, **kwargs):
        """Initialize but do not create the generation."""
        super(GenerationKeyJob, self).__init__(*args, **kwargs)
        self.lifetime = lifetime
        self.for_class = for_class
        self.generation_args = generation_args

    def key(self, *args, **kwargs):
        """Return a key that is derived only from the initial args."""
        generation_args = ':'.join([str(key) for key in self.generation_args])
        return '%s:%s:generation' % (self.for_class, generation_args)

    def fetch(self, *args, **kwargs):
        """Create a unique generation identifier."""
        return crypto.get_random_string(length=12)

    def get_constructor_kwargs(self):
        """
        Get named arguments for re-initialization.

        The async refresh task re-creates the GenerationKeyJob.
        """
        return {'lifetime': self.lifetime,
                'for_class': self.for_class,
                'generation_args': self.generation_args}


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
