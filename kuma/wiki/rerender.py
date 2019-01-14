# -*- coding: utf-8 -*-
"""Data and process for safely re-rendering documents asynchronously."""

from __future__ import unicode_literals

from datetime import datetime, timedelta
from json import loads
from uuid import uuid4

from celery.result import AsyncResult
from celery.states import ALL_STATES, PENDING, READY_STATES, SUCCESS
from django.conf import settings
from django.core.cache import cache
from django.db.models import Q
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

from kuma.core.utils import celery_queue_sizes
from kuma.users.models import User

from .models import Document


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
        if expected < params_keys:
            raise cls.InvalidData(
                'Extra param(s) %s' % ','.join(params_keys - expected))
        if expected > params_keys:
            raise cls.InvalidData(
                'Missing param(s) %s' % ','.join(expected - params_keys))

        # Initialize from the params
        init_params = {name: params[name] for name in cls.USER_FIELDS}
        instance = cls(deserialize_mode=True, **init_params)
        for name, _ in cls.STATE_FIELDS:
            setattr(instance, name, params[name])
        return instance

    def store(self, validated_data=None, cache_time=None):
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
        cache_time = cache_time or 60 * 60 * 24 * 7
        cache.set(key, data_json, cache_time)

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


class CachedDataSerializer(Serializer):
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


# Allowed states of re-render job
JOB_STATES = (
    'init',             # Job is initialized
    'waiting',          # Waiting for other jobs
    'rough_count',      # Making a rough count of docs to re-render
    'detailed_count',   # Gathering IDs of docs to re-render
    'start_chunk',      # Start async rendering of a chunk of documents
    'monitor_chunk',    # Monitor progress of async rendering
    'cool_down',        # Waiting for the queues to clear
    'done',             # Done rendering documents
    'canceled',         # Job was canceled
    'errored',          # Job stopped due to errors
    'orphaned',         # Job appears dead for unknown reasons
)


class DocumentPathSerializer(Serializer):
    """Document ID and the path, for reports."""
    doc_id = IntegerField(help_text='Document ID')
    path = CharField(help_text='Document path')


class SafeRenderJobSerializer(CachedDataSerializer):
    """Data and formatting rules for re-render jobs."""
    job_id = UUIDField(
        help_text='ID of this job',
        default=uuid4)
    version = IntegerField(
        help_text='Job format version',
        default=1)
    state = ChoiceField(
        help_text='Current re-render state',
        choices=JOB_STATES,
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
        help_text='User ID that initiated re-render',
        allow_null=True,
        default=None)
    username = CharField(
        help_text='Username that initiated re-render',
        allow_blank=True,
        default='')
    emails = ListField(
        help_text='Emails to notify at end of re-render',
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
        help_text='Time at end of re-render',
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
    recent_docs = DocumentPathSerializer(
        help_text='Recently rendered documents',
        many=True)
    errored_docs = DocumentPathSerializer(
        help_text='Documents with KumaScript errors',
        many=True)
    tasks_goal = IntegerField(
        help_text='Goal depth of tasks queue before next batch',
        min_value=1,
        default=2)
    tasks_max_seen = IntegerField(
        help_text='Maximum number of tasks seen',
        allow_null=True,
        default=None)
    tasks_current = IntegerField(
        help_text='Current depth of task queue',
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
        help_text='Size of parallel render chunks',
        min_value=1,
        default=100)
    batch_interval = IntegerField(
        help_text='Seconds to wait between batch rendering checks',
        min_value=1,
        default=5)
    stuck_time = IntegerField(
        help_text='Seconds until a render is considered stuck',
        min_value=15,
        default=120)
    error_percent = IntegerField(
        help_text='Percent of render errors to cancel job',
        min_value=1,
        max_value=100,
        default=10)

    def create(self, validated_data):
        """Create a new SafeRenderJob, used by .save()."""
        return super(self, SafeRenderJobSerializer).create(
            validated_data, SafeRenderJob)


class SafeRenderJob(CachedData):
    """A async job to render a set of wiki Documents."""

    serializer_class = SafeRenderJobSerializer

    # Fields set by the caller
    USER_FIELDS = (
        'filter_macros', 'filter_locales', 'user_id', 'username', 'emails',
        'tasks_goal', 'batch_size', 'batch_interval', 'stuck_time',
        'error_percent')
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
        ('recent_docs', []),                # ID and URL of recently rendered docs
        ('errored_docs', []),               # ID and URL of errored docs
        ('tasks_max_seen', None),           # Maximum num of tasks seen
        ('tasks_current', None),            # Current num of tasks seen
        ('canceled', False),                # True when user requests cancel
        ('canceled_by', None),              # User ID that requested cancel
    )
    ID_FIELD = 'job_id'

    # States at end of the job
    FINAL_STATES = (
        'done',             # Done rendering documents
        'canceled',         # Job was canceled
        'errored',          # Job stopped due to errors
        'orphaned',         # Job appears dead for unknown reasons
    )

    def __init__(
            self, filter_macros=None, filter_locales=None, user_id=None,
            username='', emails=None, tasks_goal=2, batch_size=100,
            batch_interval=5, stuck_time=120, error_percent=10,
            deserialize_mode=False):
        """
        Initialize the SafeRenderJob.

        Keyword Arguments:
        - filter_macros: Match docs with any of these macros (default: [])
        - filter_locales: Match docs with any of these locales (default: [])
        - user_id: User ID that initiated the job (default: None)
        - username: Username that initiated the job (default: empty)
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
        self.username = username
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
        return 'safe-render-job-%s' % job_id

    def run(self):
        """Run the next step of this job, and store the job."""

        # Set the heartbeat
        now = datetime.now()
        self.ts_heartbeat = now

        next_call = None
        if settings.MAINTENANCE_MODE or self.canceled:
            # Cancel the job
            self.finalize('canceled')
        elif self.state in ('init', 'waiting', 'rough_count'):
            # Get a SQL-based count of documents to render
            next_call = self.run_rough_count
        elif self.state == 'detailed_count':
            # Get a content-based count of documents to render
            next_call = self.run_detailed_count
        elif self.state == 'start_chunk':
            # Start rendering a chunk of documents
            next_call = self.run_start_chunk
        elif self.state == 'monitor_chunk':
            # Check if the rendered documents are complete
            next_call = self.run_monitor_chunk
        elif self.state == 'cool_down':
            # Wait for the queue to process document jobs
            next_call = self.run_cool_down
        else:
            # This job is already in a final state
            assert self.state in self.FINAL_STATES

        if next_call:
            call_again, with_timeout = next_call()
            self.store()
            timeout = self.batch_interval if with_timeout else 0
            return call_again, timeout
        else:
            return False, None

    def run_rough_count(self):
        """Get the SQL-based list of the documents to render."""
        # Update state
        self.state = 'rough_count'
        self.ts_rough_count = self.ts_heartbeat
        self.store()

        # Get rough filter
        docs = Document.objects.all()
        if self.filter_locales:
            docs = docs.filter(locale__in=self.filter_locales)
        if self.filter_macros:
            macros = self.filter_macros
            macro_q = Q(html__icontains=macros[0].lower())
            for macro in macros[1:]:
                macro_q |= Q(html__icontains=macro.lower())
            docs = docs.filter(macro_q)

        # Get the rough count, which may take a while
        self.count_rough = docs.count()
        self.ts_heartbeat = datetime.now()

        # Update the estimate from the rough count
        self.estimate = (self.ts_heartbeat +
                         timedelta(seconds=self.count_rough))

        # Initialize the batch with the SQL-based document IDs
        batch = SafeRenderBatch()
        raw_doc_ids = list(docs.order_by('id').values_list('id', flat=True))
        batch.to_filter_ids = raw_doc_ids
        batch.store()
        self.batch_id = batch.batch_id

        # Call run_detailed_count as soon as possible
        self.state = 'detailed_count'
        return True, False

    def run_detailed_count(self):
        """Get the content-based list of the documents to render."""
        # Update state
        self.state = 'detailed_count'
        self.ts_detailed_count = self.ts_heartbeat
        self.store()

        # If macros are specified, we need a detailed count
        batch = SafeRenderBatch.load(self.batch_id)
        batch.to_do_ids = []
        filter_macros = [m.lower() for m in self.filter_macros]
        for doc_id in batch.to_filter_ids:
            if filter_macros:
                # Check that the document uses the macro before rendering
                try:
                    doc = Document.objects.get(id=doc_id)
                except Document.DoesNotExist:
                    continue
                doc_macros = set([m.lower() for m in doc.extract.macro_names()])
                match = any((macro in doc_macros for macro in filter_macros))
            else:
                # Rough filter is enough to include document
                match = True

            if match:
                batch.to_do_ids.append(doc_id)

        # End of (potentially) lengthy processing, set heartbeat
        self.ts_heartbeat = datetime.now()

        # Store filtered document IDs, new estimate
        batch.to_filter_ids = []
        batch.store()
        self.count_detailed = len(batch.to_do_ids)
        self.estimate = (self.ts_heartbeat +
                         timedelta(seconds=self.count_detailed))

        # Call run_start_chunk as soon as possible
        self.state = 'start_chunk'
        return True, False

    def run_start_chunk(self):
        """Start async rendering of a chunk of documents."""
        from .tasks import render_document

        # Update state
        self.state = 'start_chunk'
        if not self.ts_render:
            self.ts_render = self.ts_heartbeat
        self.store()

        # Load the batch and documents to render
        batch = SafeRenderBatch.load(self.batch_id)
        assert batch.chunk == []
        self.estimate = (self.ts_heartbeat +
                         timedelta(seconds=len(batch.to_do_ids)))

        # If the error ratio is too high, then abort
        if self.count_errored:
            errored = float(self.count_errored)
            rendered = float(self.count_rendered)
            err_percent = 100.0 * errored / (errored + rendered)
            if err_percent >= self.error_percent:
                self.finalize('errored')
                return False, False

        # If we're done rendering, then finalize
        if len(batch.to_do_ids) == 0:
            self.finalize('done')
            return False, False

        # Pick the next chunk of IDs
        chunk_ids = batch.to_do_ids[:self.batch_size]
        batch.to_do_ids = batch.to_do_ids[self.batch_size:]

        # Start rendering
        for doc_id in chunk_ids:
            task = render_document.delay(doc_id, "no-cache", None, force=True)
            batch.chunk.append({
                'doc_id': doc_id,
                'task_id': task.id,
                'task_state': task.state,
                'change_time': self.ts_heartbeat
            })

        # Update batch and job
        batch.store()
        self.ts_heartbeat = datetime.now()
        self.count_in_progress = len(batch.chunk)

        # Check chunk status in a few seconds
        self.state = 'monitor_chunk'
        return True, True

    def run_monitor_chunk(self):
        """Check status of a chunk of rendering documents."""
        # Update state
        self.state = 'monitor_chunk'
        self.store()

        # Update rendering status
        last_change = self.ts_render  # An old time
        docs_success = []
        docs_errored = []
        docs_in_progress = []
        now = self.ts_heartbeat
        batch = SafeRenderBatch.load(self.batch_id)
        for in_progress in batch.chunk:
            doc_id = in_progress['doc_id']
            old_state = in_progress['state']
            if old_state in READY_STATES:
                # Already complete
                new_state = old_state
            else:
                # Ask Celery for new state
                render_task = AsyncResult(in_progress['task_id'])
                new_state = render_task.state
                if new_state != old_state:
                    in_progress['state'] = new_state
                    in_progress['change_time'] = now
                    last_change = now

            if new_state == SUCCESS:
                if in_progress['ks_errors'] == '':
                    # Check if kumascript rendered with errors
                    has_errors = (Document.objects.filter(id=doc_id)
                                  .exclude(rendered_errors__isnull=True)
                                  .exists())
                    in_progress['ks_errors'] = 'y' if has_errors else 'n'
                if in_progress['ks_errors'] == 'y':
                    docs_errored.append(doc_id)
                else:
                    docs_success.append(doc_id)
            elif new_state in READY_STATES:
                # READY_STATES is SUCCESS plus error states
                docs_errored.append(doc_id)
            else:
                docs_in_progress.append(doc_id)
        self.ts_heartbeat = datetime.now()

        # Are the re-render jobs stuck?
        stuck_time = timedelta(self.stuck_time)
        is_stuck = (self.ts_heartbeat - last_change) > stuck_time
        chunk_done = is_stuck or len(docs_in_progress) == 0

        if chunk_done:
            # End of render, finalize chunk
            # Move document IDs from chunks to batch categories
            docs = Document.objects.only('id', 'locale', 'slug').order_by('id')
            for doc in docs.filter(id__in=docs_errored):
                self.errored_docs.append({'doc_id': doc.id,
                                          'path': doc.get_absolute_url()})
            batch.stuck_ids.extend(docs_in_progress)
            batch.done_ids.extend(docs_success)
            batch.chunk = []

            # Update job progress counts
            self.count_errored = len(self.errored_docs)
            self.count_rendered = len(batch.done_ids)
            self.count_abandoned = len(batch.stuck_ids)
            self.count_in_progress = 0

            # Add some recently rendered docs
            self.recent_docs = []
            for doc in docs.filter(id__in=docs_success[:5]):
                self.recent_docs.append({'doc_id': doc.id,
                                         'path': doc.get_absolute_url()})

            # Next, wait for select task queues to empty
            self.update_task_counts()
            self.state = 'cool_down'
        else:
            # Continue waiting for render, update job progress counts
            self.count_errored = len(self.errored_docs) + len(docs_errored)
            self.count_rendered = len(batch.done_ids) + len(docs_success)
            self.count_abandoned = len(batch.stuck_ids)
            self.count_in_progress = len(docs_in_progress)
            self.state = 'monitor_chunk'

        # Save batch, call run_monitor_chunk or run_cool_down after delay
        batch.store()
        return True, True

    def update_task_counts(self):
        """
        Get count of tasks currently queued for processing.

        mdn_wiki - rendering tasks (might be the only one that matters)
        mdn_purgeable - mostly cacheback jobs, based on external traffic
        mdn_search - search indexing after re-rendering
        """
        sizes = celery_queue_sizes()
        purgeable_tasks = sizes.get('mdn_purgeable', 0)
        search_tasks = sizes.get('mdn_search', 0)
        wiki_tasks = sizes.get('mdn_wiki', 0)
        current = purgeable_tasks + search_tasks + wiki_tasks
        self.tasks_max_seen = max(self.tasks_max_seen, current)
        self.tasks_current = current

    def run_cool_down(self):
        """
        Wait for the rendering task queues to empty.

        Re-rendering a document starts several follow-on tasks, to extract
        in-content data and update metadata. Wait for the depth of some queues
        to die down before starting a new chunk of work.
        """
        # Update state. Don't bother storing for status, should be fast.
        self.state = 'monitor_chunk'

        # Check depth of purgable task queue
        self.update_task_counts()

        if self.tasks_current <= self.tasks_goal:
            # We're at the target depth. Start the next chunk soon.
            self.state = 'start_chunk'
            return True, False
        else:
            # Check again after a delay
            return True, True

    def finalize(self, state='done'):
        """Finalize the render job."""
        # Set the state
        assert state in self.FINAL_STATES
        self.state = state
        self.ts_done = self.ts_heartbeat

        # Finalize counts
        try:
            batch = SafeRenderBatch.load(self.batch_id)
        except SafeRenderBatch.NoData:
            batch = None
        else:
            self.count_errored = len(self.errored_docs)
            self.count_rendered = len(batch.done_ids)
            self.count_abandoned = (len(batch.to_filter_ids) +
                                    len(batch.to_do_ids) +
                                    len(batch.chunk))
            self.count_in_progress = 0

        # TODO: Email report
        self.store()

        # Update dashboard, schedule next job
        SafeRenderDashboard.get().refresh()

    def summary(self):
        """Return an English summary of the job."""

        parts = []

        # Summarize the filter
        filter_parts = []
        if self.filter_macros:
            if len(self.filter_macros) == 1:
                filter_parts.append("macros=%s" % self.filter_macros[0])
            else:
                filter_parts.append("macros=[%s]"
                                    % ", ".join(self.filter_macros))
        if self.filter_locales:
            if len(self.filter_locales) == 1:
                filter_parts.append("locales=%s" % self.filter_locales)
            else:
                filter_parts.append("locale=[%s]"
                                    % ", ".join(self.filter_locales))
        parts.append((' and '.join(filter_parts)) or 'All documents')

        # Add the requester if given
        if self.username:
            parts.append('requested by %s' % self.username)

        # Add the status and related details
        if self.state == 'init':
            age = (datetime.now() - self.ts_init).total_seconds()
            parts.append('initialized %d second%s ago'
                         % (age, '' if age == 1 else 's'))
        elif self.state == 'waiting':
            age = (datetime.now() - self.ts_init).total_seconds()
            parts.append('waiting for %d second%s'
                         % (age, '' if age == 1 else 's'))
        elif self.state == 'rough_count':
            age = (datetime.now() - (self.ts_rough_count or self.ts_heartbeat)).total_seconds()
            parts.append('estimating document count for %d second%s'
                         % (age, '' if age == 1 else 's'))
        elif self.state == 'detailed_count':
            age = (datetime.now() - self.ts_detailed_count).total_seconds()
            parts.append(('gathering filtered documents for %d second%s'
                          ' (rough count is %d document%s)')
                         % (age,
                            '' if age == 1 else 's',
                            self.count_rough,
                            '' if self.count_rough == 1 else 's'))
        elif self.state in ('start_chunk', 'monitor_chunk'):
            parts.append(('rendering %d document%s'
                          ' (%d rendered, %d errored, %d abandoned)')
                         % (self.count_detailed,
                            '' if self.count_detailed == 1 else 's',
                            self.count_rendered,
                            self.count_errored,
                            self.count_abandoned))
        elif self.state == 'cool_down':
            parts.append(('waiting for task queue to empty'
                          ' (%d current tasks, goal is %d, max seen is %d)')
                         % (self.tasks_current,
                            self.tasks_goal,
                            self.tasks_max_seen))
        elif self.state == 'done':
            duration = (self.ts_done - self.ts_render).total_seconds()
            parts.append(('rendered %d document%s in %d second%s'
                          ' (%d rendered, %d errored, %d abandoned)')
                         % (self.count_detailed,
                            '' if self.count_detailed == 1 else 's',
                            duration,
                            '' if self.duration == 1 else 's',
                            self.count_rendered,
                            self.count_errored,
                            self.count_abandoned))
        elif self.state == 'canceled':
            parts.append('canceled')
        elif self.state == 'errored':
            parts.append('errored')
        else:
            assert self.state == 'orphaned'
            parts.append('orphaned')

        return ', '.join(parts)


class DocumentInProcessSerializer(Serializer):
    """Document data for the in-process document."""
    doc_id = IntegerField(
        help_text='Document ID')
    task_id = CharField(
        help_text='Celery Task ID')
    state = ChoiceField(
        help_text='Render state of document',
        choices=ALL_STATES,
        default=PENDING)
    change_time = DateTimeField(
        help_text='Time of last state change',
        default=datetime.now)
    ks_errors = ChoiceField(
        help_text='Were there KumaScript errors?',
        choices=('', 'y', 'n'),
        default='')


class SafeRenderBatchSerializer(CachedDataSerializer):
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
        help_text='Document IDs to re-render',
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
        """Create a new SafeRenderBatch, used by .save()."""
        return super(self, SafeRenderBatchSerializer).create(
            validated_data, SafeRenderBatch)


class SafeRenderBatch(CachedData):
    """
    Store detailed data for a re-render job.

    This is kept separate from the rest of the job data because it is only
    maintained while the job is running, can be dropped at the end of the
    job, and isn't needed for the dashboard.
    """

    serializer_class = SafeRenderBatchSerializer
    USER_FIELDS = ()
    STATE_FIELDS = (
        ('batch_id', uuid4),        # UUID of this data
        ('to_filter_ids', []),      # Doc IDs before content filtering
        ('to_do_ids', []),          # Pending Document IDs
        ('stuck_ids', []),          # Doc IDs that timed out rendering
        ('done_ids', []),           # Successfully rendered Doc IDs
        ('chunk', []),              # Data for Docs being currently rendered
    )
    ID_FIELD = 'batch_id'

    @classmethod
    def cache_key(cls, batch_id):
        """Generate the cache key for storing job data."""
        assert batch_id
        return 'safe-render-batch-%s' % batch_id


class SafeRenderDashboardSerializer(CachedDataSerializer):
    """Maintain the list of SafeRenderJobs."""
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
        """Create a new SafeRenderDashboard, used by .save()."""
        return super(self, SafeRenderDashboardSerializer).create(
            validated_data, SafeRenderDashboard)


class SafeRenderDashboard(CachedData):
    """Maintain an index of SafeRenderJobs, and pick the current one."""

    serializer_class = SafeRenderDashboardSerializer

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
        return 'safe-render-dashboard'

    @classmethod
    def get(cls):
        """Load from cache or create new dashboard."""
        try:
            dashboard = cls.load()
        except SafeRenderDashboard.NoData:
            dashboard = SafeRenderDashboard()
        return dashboard

    def register_job(self, job):
        """Register a job with the dashboard, and save the job."""
        job_id = job.job_id
        assert job.state == 'init'
        assert job.job_id not in self.job_ids
        self.job_ids.append(job_id)
        self.refresh(preloaded_jobs={job_id: job})
        if job.state == 'waiting':
            # We didn't get picked as current job
            job.store()
        return job

    def refresh(self, preloaded_jobs=None):
        """
        Refresh the list of active rendering jobs

        Keyword Arguments:
        - data: Deserialized dashboard data
        - preloaded_jobs: dictionary of job IDs to loaded jobs.
        """
        from .tasks import run_safe_render_job

        # Setup processed job list, current job
        jobs = []
        current_job = None

        # Set timestamp for when a job is considered stale
        ts_stale = datetime.now() - timedelta(days=self.max_days)

        # Load job data
        job_ids = set()
        preloaded_jobs = preloaded_jobs or {}
        for job_id in self.job_ids:
            assert job_id not in job_ids
            if job_id in preloaded_jobs:
                job = preloaded_jobs[job_id]
            else:
                try:
                    job = SafeRenderJob.load(job_id)
                except SafeRenderJob.NoData:
                    job = None  # Job was deleted
            if job:
                # Delete jobs older than the stale date
                if job.ts_init < ts_stale:
                    job.delete()
                    job = None

            if job:
                # Job is valid
                jobs.append(job)
                job_ids.add(job_id)
                if job.state == 'init':
                    job.state = 'waiting'
                if job_id == self.current_job_id:
                    current_job = job

        # Is the current job done?
        if current_job and current_job.state in SafeRenderJob.FINAL_STATES:
            current_job = None

        # Pick current job if we don't have one
        if not current_job:
            in_progress = []
            waiting = []
            active_states = set((
                'rough_count',      # Making a rough count of docs to re-render
                'detailed_count',   # Gathering IDs of docs to re-render
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

        # Activate the current job if it is waiting to run
        if current_job and current_job.state == 'waiting':
            current_job.state = 'rough_count'
            current_job.store()
            run_safe_render_job.delay(current_job.job_id)

        # Save updated dashboard
        self.job_ids = list(sorted([job.job_id for job in jobs]))
        self.current_job_id = current_job.job_id if current_job else None
        self.store()


def init_rerender_job(
        macros=None, locales=None, user_id=None, emails=None,
        **advanced_options):
    """
    Initialize a re-render job.

    Optional Keyword Arguments:
    - macros: A list of macros to filter on
    - locales: A list of locales to filter on
    - user_id: The user ID that initiated the report
    - emails: Emails to get a final report
    - advanced_options: other options to SafeRenderJob
    """

    if user_id:
        username = User.objects.get(id=user_id).only('username').username
    else:
        username = ''
    job = SafeRenderJob(
        filter_macros=macros, filter_locales=locales, user_id=user_id,
        username=username, emails=emails, **advanced_options)
    dashboard = SafeRenderDashboard.get()
    dashboard.register_job(job)
    return job


# from kuma.wiki.rerender import try_it; job = try_it()


def try_it():
    job = init_rerender_job(macros=['experimental_inline'], locales=['en-US'])
    return job


def try_it2():
    dashboard = SafeRenderDashboard.get()
    dashboard.refresh()


def try_it3():
    job = init_rerender_job(macros=['IncludeSubnav'])
    return job
