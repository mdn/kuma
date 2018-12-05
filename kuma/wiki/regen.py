# -*- coding: utf-8 -*-
"""Regeneration data and utilities"""

from __future__ import unicode_literals

from datetime import datetime
from uuid import uuid4

from celery.states import ALL_STATES as CELERY_STATES
from celery.states import PENDING
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
    tasks_max_seen = IntegerField(
        help_text='Maximum number of purgable tasks seen',
        allow_null=True,
        default=None)
    tasks_current = IntegerField(
        help_text='Current depth of purgable task queue',
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
    current_job = UUIDField(
        help_text='Currently running job',
        allow_null=True,
        default=None)




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
