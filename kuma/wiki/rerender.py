# -*- coding: utf-8 -*-
"""Regeneration data and utilities"""

from __future__ import unicode_literals

from datetime import datetime, timedelta
from json import loads
from uuid import uuid4

from celery.states import ALL_STATES as CELERY_STATES
from celery.states import PENDING
from django.core.cache import cache
from rest_framework.renderers import JSONRenderer
from rest_framework.serializers import (
    BooleanField,
    CharField,
    ChoiceField,
    DateTimeField,
    EmailField,
    IntegerField,
    ListField,
    Serializer,
    UUIDField,
)


class CachedData(object):
    """Data that is JSON-serialized and stored in the cache."""

    # Implementors should set these
    serializer_class = None     # The Django REST Framework serializer class
    USER_FIELDS = None          # Attribute names set by users
    STATE_FIELDS = None         # Pairs of (name, default_value) set at creation
    ID_FIELD = None             # Name of ID field, or leave None if no ID field

    def __init__(self, deserialize_mode=False):
        """Generic init function."""
        assert not self.USER_FIELDS, "Must override if users can set fields"
        if not deserialize_mode:
            self.init_state_fields()

    @classmethod
    def cache_key(cls, data_id):
        """Generate the cache key for the data."""
        raise NotImplementedError

    def init_state_fields(self):
        """Set the state fields to initial values."""
        now = datetime.now()
        for name, default in self.STATE_FIELDS:
            if default == datetime.now:
                value = now  # Use consistant value for datetime.now()
            elif callable(default):
                value = default()
            else:
                value = default
            setattr(self, name, value)

    @classmethod
    def deserialize(cls, **params):
        """Restore complete serialized class state."""
        # Assert that params sets all the expected fields
        expected = set(cls.USER_FIELDS)
        expected |= set(name for name, _ in cls.STATE_FIELDS)
        params_keys = set(params.keys())
        assert expected >= params_keys, (
            'Missing params %s' % (expected - params_keys))
        assert params_keys >= expected, (
            'Missing params %s' % (params_keys - expected))

        # Initialize from the params
        init_params = {name: params[name] for name in cls.USER_FIELDS}
        instance = cls(deserialize_mode=True, **init_params)
        for name, _ in cls.STATE_FIELDS:
            setattr(instance, name, params[name])
        return instance

    def store(self, validated_data=None):
        """Store in the cache."""
        if validated_data is None:
            # Run through serializer to standardize formats
            serializer = self.serializer_class(self)
            data = serializer.data
        else:
            data = validated_data

        if self.ID_FIELD:
            my_id = str(getattr(self, self.ID_FIELD))
            assert str(data[self.ID_FIELD]) == my_id
            key = self.cache_key(my_id)
        else:
            key = self.cache_key(None)
        data_json = JSONRenderer().render(data)
        print('saving %s:%s\n' % (key, data_json))
        cache.set(key, data_json)

    class NoData(ValueError):
        pass

    class InvalidData(ValueError):
        pass

    @classmethod
    def load(cls, data_id=None):
        """Load from cache."""
        key = cls.cache_key(data_id)
        job_json = cache.get(key, None)
        if job_json:
            data = loads(job_json)
            serializer = cls.serializer_class(data=data)
            if not serializer.is_valid():
                raise cls.InvalidData(data, serializer.errors)
            print('loaded %s:%s\n' % (key, job_json))
            job = cls.deserialize(**serializer.validated_data)
            return job
        else:
            raise cls.NoData(data_id)

    @classmethod
    def delete_by_id(cls, data_id=None):
        """Delete from cache by ID."""
        key = cls.cache_key(data_id)
        print('deleting %s\n' % (key,))
        cache.delete(key)

    def delete(self):
        """Delete from cache."""
        if self.ID_FIELD:
            data_id = getattr(self, self.ID_FIELD)
        else:
            data_id = None
        self.delete_by_id(data_id)


class BaseSerializer(Serializer):
    """Common create / update methods for serializers."""

    def create(self, validated_data, data_class):
        """Create a new CachedData instance, used by .save()."""
        instance = data_class(**validated_data)
        instance.store(validated_data)
        return instance

    def update(self, instance, validated_data):
        """Update an existing CachedData instance, used by .save()."""
        for field in self.fields.keys():
            current = getattr(instance, field)
            setattr(instance, field, validated_data.get(field, current))
        instance.store(validated_data)
        return instance


# Allowed states of regeneration job
REGENERATION_STATES = (
    'init',             # Job is initialized
    'waiting',          # Waiting for other jobs
    'rough_count',      # Making a rough count of docs to regeneration
    'detailed_count',   # Gathering IDs of docs to regenerate
    'rendering',        # Rendering a batch of documents
    'cool_down',        # Waiting for the purgable queue to clear
    'done',             # Done rendering documents
    'canceled',         # Job was canceled
    'errored',          # Job stopped due to errors
    'orphaned',         # Job appears dead for unknown reasons
)


class RegenerationJobSerializer(BaseSerializer):
    """Data and formatting rules for regeneration jobs."""

    job_id = UUIDField(
        help_text='ID of this job',
        default=uuid4)
    version = IntegerField(
        help_text='Job format version',
        default=1)
    state = ChoiceField(
        help_text='Current regeneration state',
        choices=REGENERATION_STATES,
        default='init')
    filter_macros = ListField(
        help_text="Filter documents that include any of these macros.",
        child=CharField(),
        default=[]
    )
    filter_locales = ListField(
        help_text="Filter documents in any of these locales.",
        child=CharField(),
        default=[]
    )
    user_id = IntegerField(
        help_text='User ID that initiated regeneration',
        allow_null=True,
        default=None)
    emails = ListField(
        help_text='Emails to notify at end of regeneration',
        child=EmailField(),
        default=[])
    count_rough = IntegerField(
        help_text='Rough count of documents',
        allow_null=True,
        default=None)
    count_detailed = IntegerField(
        help_text='Detailed count of documents',
        allow_null=True,
        default=None)
    count_rendered = IntegerField(
        help_text='Count of rendered documents',
        default=0)
    count_errored = IntegerField(
        help_text='Count of errored documents',
        default=0)
    count_abandoned = IntegerField(
        help_text='Count of documents stalled in re-render',
        default=0)
    count_in_progress = IntegerField(
        help_text='Count of documents queued for re-render',
        default=0)
    ts_init = DateTimeField(
        help_text='Time at initialization',
        default=datetime.now)
    ts_heartbeat = DateTimeField(
        help_text='Time at last processing',
        default=datetime.now,
        allow_null=True)
    ts_rough_count = DateTimeField(
        help_text='Time at start of rough count of Documents',
        default=None,
        allow_null=True)
    ts_detailed_count = DateTimeField(
        help_text='Time at start of detailed count of Documents',
        default=None,
        allow_null=True)
    ts_render = DateTimeField(
        help_text='Time at start of rendering',
        default=None,
        allow_null=True)
    ts_done = DateTimeField(
        help_text='Time at end of regeneration',
        default=None,
        allow_null=True)
    estimate = DateTimeField(
        help_text='Estimated completion time',
        allow_null=True,
        default=None)
    batch_id = UUIDField(
        help_text='ID of current batch job',
        allow_null=True,
        default=None)
    recent_docs = ListField(
        help_text='URLs of recently rendered documents',
        child=CharField(),
        default=[])
    errored_ids = ListField(
        help_text='IDs of documents with KumaScript errors',
        child=IntegerField(),
        default=[])
    tasks_goal = IntegerField(
        help_text='Goal depth of purgable tasks queue before next batch',
        min_value=1,
        default=2)
    tasks_max_seen = IntegerField(
        help_text='Maximum number of purgable tasks seen',
        allow_null=True,
        default=None)
    tasks_current = IntegerField(
        help_text='Current depth of purgable task queue',
        allow_null=True,
        default=None)
    canceled = BooleanField(
        help_text='Did the user request cancelling the job?',
        default=False)
    canceled_by = IntegerField(
        help_text='User ID that canceled the job',
        allow_null=True,
        default=None)
    batch_size = IntegerField(
        help_text='Size of parallel rerender chunks',
        min_value=1,
        default=100)
    batch_interval = IntegerField(
        help_text='Seconds to wait between batch rendering checks',
        min_value=1,
        default=5)
    stuck_time = IntegerField(
        help_text='Seconds until a rerender is considered stuck',
        min_value=15,
        default=120)
    error_percent = IntegerField(
        help_text='Percent of render errors to cancel job',
        min_value=1,
        max_value=100,
        default=10)

    def create(self, validated_data):
        """Create a new RegenerationJob, used by .save()."""
        return super(self, RegenerationJobSerializer).create(
            validated_data, RegenerationJob)


class RegenerationJob(CachedData):
    """A async job to render a set of wiki Documents."""

    serializer_class = RegenerationJobSerializer

    # Fields set by the caller
    USER_FIELDS = (
        'filter_macros', 'filter_locales', 'user_id', 'emails', 'tasks_goal',
        'batch_size', 'batch_interval', 'stuck_time', 'error_percent')
    # Fields initialized at the start of the job
    STATE_FIELDS = (
        ('job_id', uuid4),                  # UUID of this job
        ('version', 1),                     # Job data version
        ('state', 'init'),                  # Job state
        ('count_rough', None),              # Rough SQL count of docs
        ('count_detailed', None),           # Detailed count from content
        ('count_rendered', 0),              # Rendered docs
        ('count_errored', 0),               # Errored docs
        ('count_abandoned', 0),             # Stalled or never started
        ('count_in_progress', 0),           # Queued for rendering
        ('ts_init', datetime.now),          # Time at job intialization
        ('ts_heartbeat', datetime.now),     # Time at last processing
        ('ts_rough_count', None),           # Start of rough count
        ('ts_detailed_count', None),        # Start of detailed count
        ('ts_render', None),                # Start of rendering
        ('ts_done', None),                  # Rendering complete or stopped
        ('estimate', None),                 # Estimated completion time
        ('batch_id', None),                 # UUID of detailed batch data
        ('recent_docs', []),                # URLs of recently rendered docs
        ('errored_ids', []),                # IDs of errored docs
        ('tasks_max_seen', None),           # Maximum num of tasks seen
        ('tasks_current', None),            # Current num of tasks seen
        ('canceled', False),                # True when user requests cancel
        ('canceled_by', None),              # User ID that requested cancel
    )
    ID_FIELD = 'job_id'

    def __init__(
            self, filter_macros=None, filter_locales=None, user_id=None,
            emails=None, tasks_goal=2, batch_size=100, batch_interval=5,
            stuck_time=120, error_percent=10, deserialize_mode=False):
        """
        Initialize the RegenerationJob.

        Keyword Arguments:
        - filter_macros: Match docs with any of these macros (default: [])
        - filter_locales: Match docs with any of these locales (default: [])
        - user_id: User ID that initiated the job (default: None)
        - emails: Emails to send final report (default: [])
        - tasks_goal: Size of task queue to start next batch (default: 2)
        - batch_size: Size of parallel render batch (default: 100)
        - batch_interval: Seconds to wait between batch checks (default: 5)
        - stuck_time: Seconds until a render is considered stuck (default: 120)
        - error_percent: Percent of render errors to cancel job (default: 10)
        - deserialize_mode: If True, deserializer will initialize other
          parameters, so don't set them.
        """
        self.filter_macros = filter_macros or []
        self.filter_locales = filter_locales or []
        self.user_id = user_id
        self.emails = emails or []
        self.tasks_goal = tasks_goal
        self.batch_size = batch_size
        self.batch_interval = batch_interval
        self.stuck_time = stuck_time
        self.error_percent = error_percent

        if not deserialize_mode:
            self.init_state_fields()

    @classmethod
    def cache_key(cls, job_id):
        """Generate the cache key for storing job data."""
        assert job_id
        return 'regen-job-%s' % job_id

    def run(self):
        """Run the next step of this job."""
        print("I'm running!")


class DocumentInProcessSerializer(Serializer):
    """Document data for the in-process document."""
    doc_id = IntegerField(
        help_text='Document ID')
    task_id = CharField(
        help_text='Celery Task ID')
    state = ChoiceField(
        help_text='Render state of document',
        choices=CELERY_STATES,
        default=PENDING)
    change_time = DateTimeField(
        help_text='Time of last state change',
        default=datetime.now)


class RegenerationBatchSerializer(Serializer):
    """
    Detailed document data for a job.

    This is a seperate data packet to minimimze the size of the general
    job JSON.
    """
    batch_id = UUIDField(
        help_text='ID of current batch job',
        default=uuid4)
    to_filter_ids = ListField(
        help_text='Document IDs to test for further filtering',
        child=IntegerField(),
        default=[])
    to_do_ids = ListField(
        help_text='Document IDs to regenerate',
        child=IntegerField(),
        default=[])
    errored_ids = ListField(
        help_text='Document IDs with rendering errors',
        child=IntegerField(),
        default=[])
    stuck_ids = ListField(
        help_text='Document IDs with stuck rendering tasks',
        child=IntegerField(),
        default=[])
    done_ids = ListField(
        help_text='Document IDs done rendering',
        child=IntegerField(),
        default=[])
    chunk = DocumentInProcessSerializer(
        help_text='Documents currently being rendered',
        many=True)

    def create(self, validated_data):
        """Create a new RegenerationBatch, used by .save()."""
        return super(self, RegenerationBatchSerializer).create(
            validated_data, RegenerationBatch)


class RegenerationBatch(CachedData):
    """
    Store detailed data for a regeneration job.

    This is kept separate from the rest of the job data because it is only
    maintained while the job is running, can be dropped at the end of the
    job, and isn't needed for the dashboard.
    """

    serializer_class = RegenerationBatchSerializer
    USER_FIELDS = ()
    STATE_FIELDS = (
        ('batch_id', uuid4),        # UUID of this data
        ('to_filter_ids', []),      # Doc IDs before content filtering
        ('to_do_ids', []),          # Pending Document IDs
        ('errored_ids', []),        # Doc IDs with KumaScript errors
        ('stuck_ids', []),          # Doc IDs that timed out rendering
        ('done_ids', []),           # Successfully rendered Doc IDs
        ('chunk', []),              # Data for Docs being currently rendered
    )
    ID_FIELD = 'batch_id'

    @classmethod
    def cache_key(cls, batch_id):
        """Generate the cache key for storing job data."""
        assert batch_id
        return 'regen-batch-%s' % batch_id


class RegenerationDashboardSerializer(Serializer):
    """Maintain the list of RegenerationJobs."""
    job_ids = ListField(
        help_text='Known jobs',
        child=UUIDField(),
        default=[])
    current_job_id = UUIDField(
        help_text='Currently running job',
        allow_null=True,
        default=None)
    max_days = IntegerField(
        help_text='Days to retain jobs',
        allow_null=True,
        default=7)

    def create(self, validated_data):
        """Create a new RegenerationDashboard, used by .save()."""
        return super(self, RegenerationDashboardSerializer).create(
            validated_data, RegenerationDashboard)


class RegenerationDashboard(CachedData):
    """Maintain an index of RegenerationJobs, and pick the current one."""

    serializer_class = RegenerationDashboardSerializer

    USER_FIELDS = ()
    STATE_FIELDS = (
        ('job_ids', []),            # UUIDs of known jobs
        ('current_job_id', None),   # Currently running job, if any
        ('max_days', 7),            # Number of days to retain jobs
    )

    @classmethod
    def cache_key(cls, dashboard_id=None):
        """Generate the cache key for storing dashabords."""
        assert dashboard_id is None
        return 'regen-dashboard'

    @classmethod
    def get(cls):
        """Load from cache or create new dashboard."""
        try:
            dashboard = cls.load()
        except RegenerationDashboard.NoData:
            dashboard = RegenerationDashboard()
        return dashboard

    def register_job(self, job):
        """Register a job with the dashboard, and save the job."""
        job_id = job.job_id
        assert job.state == 'init'
        assert job.job_id not in self.job_ids
        self.job_ids.append(job_id)
        self.refresh(preloaded_jobs={job_id: job})
        job.store()
        return job

    def refresh(self, max_time=None, preloaded_jobs=None):
        """
        Refresh the list of active rendering jobs

        Keyword Arguments:
        - data: Deserialized dashboard data
        - max_time: A max job time (default = 1 week)
        - preloaded_jobs: dictionary of job IDs to loaded jobs.
        """

        # Load job data
        jobs = []
        job_ids = set()
        preloaded_jobs = preloaded_jobs or {}
        for job_id in self.job_ids:
            assert job_id not in job_ids
            if job_id in preloaded_jobs:
                job = preloaded_jobs[job_id]
            else:
                try:
                    job = RegenerationJob.load(job_id)
                except RegenerationJob.NoData:
                    job_id = None  # Job was deleted
            if job_id:
                job_ids.add(job_id)
                jobs.append(job)
                if job.state == 'init':
                    job.state = 'waiting'

        # Find the current job
        current_job = None
        if self.current_job_id:
            for job in jobs:
                if job.job_id == self.current_job_id:
                    assert not current_job
                    current_job = job
        if self.current_job_id and not current_job:
            # Invalid current job
            self.current_job_id = None

        # Is the current job done?
        final_states = ('done', 'canceled', 'errored', 'orphaned')
        if current_job and current_job.state in final_states:
            self.current_job_id = None

        # Drop jobs over the maximum age
        now = datetime.now()
        max_time = max_time or timedelta(days=7)
        oldest = now - max_time
        for job in jobs:
            start = job.ts_init
            if start < oldest:
                if job.job_id == self.current_job_id:
                    self.current_job_id = None
                job.delete()

        # Pick current job
        if not self.current_job_id:
            in_progress = []
            waiting = []
            active_states = set((
                'rough_count',      # Making a rough count of docs to regeneration
                'detailed_count',   # Gathering IDs of docs to regenerate
                'rendering',        # Rendering a batch of documents
                'cool_down',        # Waiting for the purgable queue to clear
            ))
            for job in jobs:
                if job.state in active_states:
                    in_progress.append((job.ts_init, job))
                elif job.state == 'waiting':
                    waiting.append((job.ts_init, job))
            candidates = sorted(in_progress) + sorted(waiting)
            if candidates:
                current_job = candidates[0][1]
                self.current_job_id = current_job.job_id

        # Activate the current job if it is waiting to run
        if current_job and current_job.state == 'waiting':
            current_job.run()

        # Save updated dashboard
        self.store()


def init_regen_job(macros=None, locales=None, user_id=None, emails=None,
                   batch_size=100, error_percent=10, wait_tasks=2):
    """
    Initialize a re-render job.

    Optional Keyword Arguments:
    - macros: A list of macros to filter on
    - locales: A list of locales to filter on
    - user_id: The user ID that initiated the report
    - emails: Emails to get a final report
    - batch_size: How many documents to render in a batch
    - error_percent: A integer in range (0, 100], to abort due to errors
    - wait_tasks: The max number of pending tasks in the purgable queue
      before starting a new chunk
    """

    job = RegenerationJob(
        filter_macros=macros, filter_locales=locales, user_id=user_id,
        emails=emails, batch_size=batch_size, error_percent=error_percent,
        wait_tasks=wait_tasks)
    dashboard = RegenerationDashboard()
    dashboard.register_job(job)
    return job


# from kuma.wiki.rerender import try_it; job = try_it()


def try_it():
    job = RegenerationJob(filter_macros=['experimental_inline'],
                          filter_locales=['en-US'])
    dashboard = RegenerationDashboard.get()
    dashboard.register_job(job)
    return job


def try_it2():
    dashboard = RegenerationDashboard.get()
    dashboard.refresh()
