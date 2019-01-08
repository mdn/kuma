# -*- coding: utf-8 -*-
"""
Re-render documents without overwhelming the queues.
"""
from datetime import datetime
from time import sleep

from django.core.management.base import BaseCommand, CommandError

from kuma.wiki.rerender import (init_rerender_job, SafeRenderDashboard,
                                SafeRenderJob)


class Command(BaseCommand):
    help = 'Re-render wiki documents while keeping editing responsive'

    def add_arguments(self, parser):
        parser.add_argument('--all',
                            action='store_true',
                            help='Re-render all documents')
        parser.add_argument('--background',
                            action='store_true',
                            help='Exit after initializing job')
        parser.add_argument('--macro',
                            help='Filter on documents using this macro')
        parser.add_argument('--macros',
                            help=('Filter on documents using these macros'
                                  ' (comma-separated list)'))
        parser.add_argument('--locale',
                            help='Filter on documents in this locale')
        parser.add_argument('--locales',
                            help=('Filter on documents in these locales'
                                  ' (comma=separated list)'))

        adv = parser.add_argument_group('advanced options')
        adv.add_argument('--email',
                         help='Send final report to this email')
        adv.add_argument('--emails',
                         help=('Send final report to these emails'
                               ' (comma-separated list)'))
        adv.add_argument('--user-id',
                         type=int,
                         default=None,
                         help='User ID that requested rerendering')
        adv.add_argument('--tasks-goal',
                         type=int,
                         default=2,
                         help=('Goal depth of tasks queue before next batch'
                               ' (default 2 pending tasks)'))
        adv.add_argument('--batch-size',
                         type=int,
                         default=100,
                         help=('Size of parallel render chunks'
                               ' (default 100 parallel renders)'))
        adv.add_argument('--batch-interval',
                         type=int,
                         default=5,
                         help=('Seconds to wait between rendering checks'
                               ' (default 5 seconds)'))
        adv.add_argument('--stuck-time',
                         type=int,
                         default=120,
                         help=('Seconds before a render is considered stuck'
                               ' (default 120 seconds w/o status change)'))
        adv.add_argument('--error_percent',
                         type=int,
                         default=10,
                         help=('Percent of render errors to cancel job'
                               ' (default 10%% of rendered documents)'))

    def handle(self, *args, **options):
        filtered = False

        # Optionally filter by locales
        locales = None
        if options['locale'] and options['locales']:
            raise CommandError('Specify --locale or --locales, not both')
        if options['locale']:
            filtered = True
            locales = [options['locale']]
        elif options['locales']:
            filtered = True
            locales = [l.strip() for l in options['locales'].split(',')]

        # Optionally filter by macros
        macros = None
        if options['macro'] and options['macros']:
            raise CommandError('Specify --macro or --macros, not both')
        if options['macro']:
            filtered = True
            macros = [options['macro']]
        elif options['macros']:
            filtered = True
            macros = [m.strip() for m in options['macros'].split(',')]

        # Require --all to rerender all documents
        if not filtered and not options['all']:
            raise CommandError('Specify a filter or --all')

        # Advanced options - email
        emails = None
        if options['email'] and options['emails']:
            raise CommandError('Specify --email or --emails, not both')
        if options['email']:
            emails = options['email']
        elif options['emails']:
            emails = [e.strip() for e in options['emails'].split(',')]

        # Other advanced options
        user_id = options['user_id'] or None
        tasks_goal = options['tasks_goal']
        batch_size = options['batch_size']
        batch_interval = options['batch_interval']
        stuck_time = options['stuck_time']
        error_percent = options['error_percent']

        verbosity = options['verbosity']
        verbose = verbosity >= 1

        job = init_rerender_job(
            macros=macros,
            locales=locales,
            emails=emails,
            user_id=user_id,
            tasks_goal=tasks_goal,
            batch_size=batch_size,
            batch_interval=batch_interval,
            stuck_time=stuck_time,
            error_percent=error_percent)

        if verbose >= 1:
            self.stdout.write('Initialized render job %s' % job.job_id)

        if options['background']:
            return

        while job.state not in SafeRenderJob.FINAL_STATES:
            sleep(5)
            job = SafeRenderJob.load(job.job_id)
            if verbose:
                self.stdout.write(
                    ('%s: rough:%s detailed:%s rendered:%s errored:%s'
                     ' abandoned:%s in_progress:%s')
                    % (job.state, job.count_rough, job.count_detailed,
                       job.count_rendered, job.count_errored,
                       job.count_abandoned, job.count_in_progress))
            if job.state == 'waiting':
                dashboard = SafeRenderDashboard.get()
                dashboard.refresh()

        self.stdout.write(('Rendered %d docs, %d left unrendered, %d errored,'
                           ' in %d seconds.')
                          % (job.count_rendered,
                             job.count_abandoned,
                             job.count_errored,
                             (datetime.now() - job.ts_init).seconds))
        if job.errored_docs:
            self.stderr.write('Rendering errors on these documents:')
            for count, doc in enumerate(job.errored_docs):
                self.stderr.write('%d: %s (%d)'
                                  % (count, doc['path'], doc['doc_id']))
