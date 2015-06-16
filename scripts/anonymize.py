#!/usr/bin/env python
"""
This script performs all the steps needed to produce an anonymized DB dump:

    * Produce a dump of the original DB
    * Import the dump into a temporary DB
    * Run anonymize.sql on the temporary DB
    * Produce an anonymized dump from the temporary DB
    * Drop the temporary DB
    * Delete the dump of the original DB
"""
from datetime import datetime
import os
import os.path
import sys
from textwrap import dedent
from optparse import OptionParser

#
# We don't just dump everything, because every new table needs to be reviewed
# with regards to santizing.
#
# Whenever a new table is created, add appropriate steps to anonymize.sql and
# then add the table here.
#
TABLES_TO_DUMP=[x.strip() for x in """
    actioncounters_actioncounterunique
    actioncounters_testmodel
    auth_group
    auth_group_permissions
    auth_message
    auth_permission
    auth_user
    auth_user_groups
    auth_user_user_permissions
    authkeys_key
    authkeys_keyaction
    constance_config
    contentflagging_contentflag
    dashboards_wikidocumentvisits
    demos_submission
    devmo_calendar
    devmo_event
    django_admin_log
    django_cache
    django_content_type
    django_session
    django_site
    djcelery_crontabschedule
    djcelery_intervalschedule
    djcelery_periodictask
    djcelery_periodictasks
    djcelery_taskstate
    djcelery_workerstate
    feeder_bundle
    feeder_bundle_feeds
    feeder_entry
    feeder_feed
    gallery_image
    gallery_video
    schema_version
    soapbox_message
    tagging_tag
    tagging_taggeditem
    taggit_tag
    taggit_taggeditem
    threadedcomments_freethreadedcomment
    threadedcomments_testmodel
    threadedcomments_threadedcomment
    tidings_watch
    user_profiles
    waffle_flag
    waffle_flag_groups
    waffle_flag_users
    waffle_sample
    waffle_switch
    wiki_attachment
    wiki_attachmentrevision
    wiki_document
    wiki_documentattachment
    wiki_documenttag
    wiki_editortoolbar
    wiki_helpfulvote
    wiki_reviewtag
    wiki_reviewtaggedrevision
    wiki_revision
    wiki_taggeddocument
""".splitlines() if x.strip()]


def print_info(s):
    if not opts.quiet: print s


def print_debug(s):
    if not opts.quiet and opts.debug: print s


def sysprint(command):
    """ Helper to print all system commands in debug mode """
    print_debug("command: %s" % command)
    os.system(command)


def main():
    now = datetime.now().strftime('%Y%m%d')

    usage = """\
        %%prog [options] DB_NAME

        Performs the steps needed to produce an anonymized DB dump.

        Examples:

        %%prog mdn_prod
            Connect to 127.0.0.1 as root, no password.
            Dump "mdn_prod", import to temporary table.
            Produce mdn_prod-anon-%(now)s.sql.gz
            Both the temporary table and the input dump are deleted.

        %%prog -i downloaded-dump.sql.gz
            Connect to 127.0.0.1 as root, no password.
            Import downloaded-dump.sql.gz.
            Produce mdn_prod-anon-%(now)s.sql.gz
            Input dump is not deleted.
    """ % dict(
        now=now
    )
    options = OptionParser(dedent(usage.rstrip()))

    options.add_option('-u', '--user',
                       default='root',
                       help='MySQL user name')
    options.add_option('-p', '--password',
                       default='',
                       help='MySQL password')
    options.add_option('-H', '--host',
                       default='127.0.0.1',
                       help='MySQL host')
    options.add_option('-i', '--input',
                       help='Input SQL dump filename')
    options.add_option('-o', '--output',
                       help='Output SQL dump filename')
    options.add_option('-q', '--quiet',
                       action='store_true',
                       help='Quiet all output')
    options.add_option('-D', '--debug',
                       action='store_true',
                       help='Enable debug output')

    options.add_option('--skip-input-dump',
                       action='store_true',
                       help='Skip the initial input DB dump')
    options.add_option('--skip-temp-create',
                       action='store_true',
                       help='Skip creation of the temporary DB')
    options.add_option('--skip-temp-import',
                       action='store_true',
                       help='Skip import of the input DB dump into the '
                            'temporary DB')
    options.add_option('--skip-anonymize',
                       action='store_true',
                       help='Skip anonymization of the temporary DB')
    options.add_option('--skip-output-dump',
                       action='store_true',
                       help='Skip the post-anonymization DB dump')
    options.add_option('--skip-drop-temp-db',
                       action='store_true',
                       help='Skip dropping the temporary DB')
    options.add_option('--skip-delete-input',
                       action='store_true',
                       help='Skip deleting the input DB dump')

    global opts, args
    (opts, args) = options.parse_args()

    if len(args) < 1:
        options.error("Need an input DB name")

    input_db = args[0]

    base_dir = os.path.dirname(__file__)

    mysql_conn = '-u%(user)s %(password)s -h%(host)s' % dict(
        user=opts.user,
        password=opts.password and ('-p%s' % opts.password) or '',
        host=opts.host,
    )

    if opts.input:
        input_dump_fn = opts.input
    else:
        input_dump_fn = '%s-%s.sql.gz' % (input_db, now)

    output_dump_fn = '%s-anon-%s.sql.gz' % (input_db, now)

    # TODO: replace dump, create, import with mysqldbcopy
    # https://dev.mysql.com/doc/mysql-utilities/1.3/en/mysqldbcopy.html
    if not opts.skip_input_dump and not opts.input:
        print_info("Dumping input DB to %s" % input_dump_fn)
        dump_cmd = ('mysqldump %(mysql_conn)s %(input_db)s %(tables)s | '
                    'gzip > %(input_dump_fn)s' % dict(
            mysql_conn=mysql_conn,
            input_db=input_db, tables=' '.join(TABLES_TO_DUMP),
            input_dump_fn=input_dump_fn
        ))
        print_debug('\t%s' % dump_cmd)
        sysprint(dump_cmd)

    temp_db = '%s_anontmp_%s' % (input_db, now)

    if not opts.skip_temp_create:
        print_info('Creating temporary DB %s' % temp_db)
        sysprint('mysqladmin %(mysql_conn)s -f drop %(temp_db)s' %
                  dict(mysql_conn=mysql_conn, temp_db=temp_db))
        sysprint('mysqladmin %(mysql_conn)s create %(temp_db)s' %
                  dict(mysql_conn=mysql_conn, temp_db=temp_db))

    if not opts.skip_temp_import:
        print_info('Importing the input dump into the temporary DB')
        sysprint('cat %(input_dump_fn)s | gzip -dc | mysql %(mysql_conn)s '
                  '%(temp_db)s' % dict(
            input_dump_fn=input_dump_fn, mysql_conn=mysql_conn,
            temp_db=temp_db
        ))

    if not opts.skip_anonymize:
        anon_sql_fn = os.path.join(base_dir, 'anonymize.sql')
        print_info('Applying %s to the temporary DB' % anon_sql_fn)
        sysprint('cat %(anon_sql_fn)s | mysql %(mysql_conn)s '
                  '%(temp_db)s' % dict(
            anon_sql_fn=anon_sql_fn, mysql_conn=mysql_conn,
            temp_db=temp_db
        ))

    if not opts.skip_output_dump:
        print_info("Dumping temporary DB to %s" % output_dump_fn)
        dump_cmd = ('mysqldump %(mysql_conn)s %(temp_db)s | '
                    'gzip > %(output_dump_fn)s' % dict(
            mysql_conn=mysql_conn, temp_db=temp_db,
            output_dump_fn=output_dump_fn
        ))
        print_debug('\t%s' % dump_cmd)
        sysprint(dump_cmd)

    if not opts.skip_drop_temp_db:
        print_info("Dropping temporary db %s" % temp_db)
        sysprint('mysqladmin %(mysql_conn)s -f drop %(temp_db)s' %
                  dict(mysql_conn=mysql_conn, temp_db=temp_db))

    if not opts.skip_delete_input and not opts.input:
        print_info('Deleting input DB dump %s' % input_dump_fn)
        os.remove(input_dump_fn)


if __name__ == '__main__':
    main()
