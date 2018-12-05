# -*- coding: utf-8 -*-
"""Regeneration data and utilities"""

from __future__ import unicode_literals

from datetime import datetime, timedelta
from json import loads
from uuid import uuid4

from celery.states import ALL_STATES as CELERY_STATES
from celery.states import PENDING
from django.cache import cache
from rest_framework.renderers import JSONRenderer
from rest_framework.serializers import (
    BooleanField,
    CharField,
    ChoiceField,
    EmailField,
    IntegerField,
    ListField,
    Serializer,
    TimeField,
    UUIDField,
)


class BaseSerializer(Serializer):
    """Helper utilities for JSON serializable data."""
    pass


class FilterParams(BaseSerializer):
    """The filter specified by the user."""
    macros = ListField(
        help_text="Filter documents that include any of these macros.",
        child=CharField(),
        default=[]
    )
    locales = ListField(
        help_text="Filter documents in any of these locales.",
        child=CharField(),
        default=[]
    )


class Timestamps(BaseSerializer):
    """Timestamps for regeneration events."""
    init = TimeField(
        help_text='Time at initialization',
        default=datetime.now)
    heartbeat = TimeField(
        help_text='Time at last processing',
        default=datetime.now,
        allow_null=True)
    rough_count = TimeField(
        help_text='Time at start of rough count of Documents',
        default=None,
        allow_null=True)
    detailed_count = TimeField(
        help_text='Time at start of detailed count of Documents',
        default=None,
        allow_null=True)
    render = TimeField(
        help_text='Time at start of rendering',
        default=None,
        allow_null=True)
    done = TimeField(
        help_text='Time at end of regeneration',
        allow_null=True)


class DocumentCounts(BaseSerializer):
    """Counts of re-rendered documents"""
    rough = IntegerField(
        help_text='Rough count of documents',
        allow_null=True,
        default=None)
    detailed = IntegerField(
        help_text='Detailed count of documents',
        allow_null=True,
        default=None)
    rendered = IntegerField(
        help_text='Count of re-rendered documents',
        default=0)
    errored = IntegerField(
        help_text='Count of errored documents',
        default=0)
    abandoned = IntegerField(
        help_text='Count of documents stalled in re-render',
        default=0)
    in_progress = IntegerField(
        help_text='Count of documents queued for re-render',
        default=0)


class RegenerationJob(BaseSerializer):
    """Data for regeneration jobs."""
    STATES = (
        'init',             # Job is initialized
        'waiting',          # Waiting for other jobs
        'rough_count',      # Making a rough count of docs to regeneration
        'detailed_count',   # Gathering IDs of docs to regenerate
        'rendering',        # Rendering a batch of documents
        'cool_down',        # Waiting for the purgable queue to clear
        'done',             # Done rendering documents
        'cancelled',        # Job was cancelled
        'errored',          # Job stopped due to errors
        'orphaned',         # Job appears dead for unknown reasons
    )

    job_id = UUIDField(
        help_text='ID of this job',
        format='hex',
        default=uuid4)
    version = IntegerField(
        help_text='Job format version',
        default=1)
    filter_params = FilterParams(
        help_text='Filter parameters',
        default=[])
    state = ChoiceField(
        help_text='Current regeneration state',
        choices=STATES,
        default='init')
    user_id = IntegerField(
        help_text='User ID that initiated regeneration',
        allow_null=True,
        default=None)
    emails = ListField(
        help_text='Emails to notify at end of regeneration',
        child=EmailField(),
        default=[])
    counts = DocumentCounts(
        help_text='Counts of rerendered documents',
        default={})
    timestamps = Timestamps(
        help_text='Timestamps for this job',
        default={})
    estimate = TimeField(
        help_text='Estimated completion time',
        allow_null=True,
        default=None)
    batch_id = UUIDField(
        help_text='ID of current batch job',
        format='hex',
        allow_null=True,
        default=None)
    recent_docs = ListField(
        help_text='URLs of recently rendered documents',
        child=CharField(),
        default=[])
    tasks_goal = IntegerField(
        help_text='Goal depth of purgable tasks queue before next batch',
        min_value=1)
    tasks_max_seen = IntegerField(
        help_text='Maximum number of purgable tasks seen',
        allow_null=True,
        default=None)
    tasks_current = IntegerField(
        help_text='Current depth of purgable task queue',
        allow_null=True,
        default=None)
    cancelled = BooleanField(
        help_text='Did the user request cancelling the job?',
        default=False)
    cancelled_by = IntegerField(
        help_text='User ID that cancelled the job',
        allow_null=True,
        default=None)
    batch_size = IntegerField(
        help_text='Size of parallel rerender chunks',
        min_value=1)
    error_percent = IntegerField(
        help_text='Percent of render errors to cancel job',
        min_value=1,
        max_value=100)


class DocumentInProcess(BaseSerializer):
    """Document data for the in-process document."""
    doc_id = IntegerField(
        help_text='Document ID')
    task_id = CharField(
        help_text='Celery Task ID')
    state = ChoiceField(
        help_text='Render state of document',
        choices=CELERY_STATES,
        default=PENDING)
    change_time = TimeField(
        help_text='Time of last state change',
        default=datetime.now)


class RegenerationBatch(BaseSerializer):
    """
    Detailed document data for a job.

    This is a seperate data packet to minimimze the size of the general
    job JSON.
    """
    batch_id = UUIDField(
        help_text='ID of current batch job',
        format='hex',
        default=uuid4)
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
    chunk = ListField(
        help_text='Documents currently being rendered',
        child=DocumentInProcess(),
        default=[])


class RegenerationDashboard(BaseSerializer):
    """Maintain the list of RegenerationJobs."""
    job_ids = ListField(
        help_text='Known jobs',
        child=UUIDField(),
        default=[])
    current_job_id = UUIDField(
        help_text='Currently running job',
        allow_null=True,
        default=None)


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

    data = {
        'filter_params': {
            'macros': macros or [],
            'locales': locales or [],
        },
        'user_id': user_id,
        'emails': emails or [],
        'batch_size': batch_size,
        'error_percent': error_percent,
        'tasks_goal': wait_tasks
    }
    job = RegenerationJob(data=data)
    if not job.is_valid():
        raise ValueError('Invalid parameters', job.errors)

    job_id = job.job_id
    store_job(job.validated_data)
    register_job(job_id)
    return job_id


def load_job(job_id):
    """Load a job from the cache."""
    key = 'regen_job_%s' % job_id
    job_json = cache.get(key, None)
    if job_json:
        data = loads(job_json)
        job = RegenerationJob(data=data)
        if not job.is_valid():
            raise ValueError('Invalid data', job.errors)
        return job.validated_data
    else:
        raise ValueError('Job not found', job_id)


def store_job(job_data):
    """Store a job in the cache."""
    job_id = job_data['job_id']
    key = 'regen_job_%s' % job_id
    cache.set(key, JSONRenderer().render(job_data))


def delete_job(job_id):
    """Remove a job by ID."""
    key = 'regen_job_%s' % job_id
    cache.delete(key)


def register_job(job_id):
    """Add a job to the dashboard."""
    dashboard = load_dashboard()
    if job_id not in dashboard['job_ids']:
        dashboard['job_ids'].append(job_id)
        dashboard = refresh_dashboard(dashboard)
        store_dashboard(dashboard)


def load_dashboard():
    """Load or create the job dashboard"""
    dashboard_json = cache.get('regen_job_dashboard', {})
    data = loads(dashboard_json)
    dashboard = RegenerationDashboard(data=data)
    if not dashboard.is_valid():
        raise ValueError('Invalid data', dashboard.errors)
    return dashboard.validated_data


def store_dashboard(data):
    """Store a dashboard in the cache"""
    cache.set('regen_job_dashboard', data)


def refresh_dashboard(data, max_time=None):
    """
    Refresh the list of active rendering jobs

    Keyword Arguments:
    - data: Deserialized dashboard data
    - max_time: A max job time (default = 1 week)
    """
    jobs = []
    job_ids = set()
    for job_id in data['job_ids']:
        assert job_id not in job_ids
        job_ids.add(job_id)
        job = load_job(job_id)
        jobs.append(job)

    # Find the current job
    current_job_id = data['current_job_id']
    if current_job_id:
        for job in jobs:
            if job['job_id'] == current_job_id:
                assert not current_job
                current_job = job

    # Is the current job done?
    if current_job and current_job['state'] == 'done':
        current_job_id = None

    # Drop jobs over the maximum age
    now = datetime.now()
    max_time = max_time or timedelta(days=7)
    oldest = now - max_time
    for job in jobs:
        start = job['timestamps']['init']
        if start > oldest:
            job_id = job['job_id']
            delete_job(job_id)
            if job_id == current_job_id:
                current_job_id = None

    # Pick current job
    if not current_job_id:
        in_progress = []
        waiting = []
        active_states = set(
            'rough_count',      # Making a rough count of docs to regeneration
            'detailed_count',   # Gathering IDs of docs to regenerate
            'rendering',        # Rendering a batch of documents
            'cool_down',        # Waiting for the purgable queue to clear
        )
        for job in jobs:
            if job['state'] in active_states:
                in_progress.append((job['timestamps']['init'], job))
            elif job['state'] == 'waiting':
                waiting.append((job['timestamps']['init'], job))
        candidates = sorted(in_progress) + sorted(waiting)
        if candidates:
            current_job = candidates[0][1]
            current_job_id = current_job['job_id']

    # Run current job
    return data


def try_it():
    import pprint
    job = RegenerationJob(data={})
    job.is_valid()
    pprint.pprint(job.data)
    pprint.pprint(job.errors)
    jdata = job.data
    new_job = RegenerationJob(data=jdata)
    new_job.is_valid()
    pprint.pprint(new_job.data)
    pprint.pprint(new_job.errors)

    batch = RegenerationBatch(data={})
    batch.is_valid()
    pprint.pprint(batch.data)
    pprint.pprint(batch.errors)
