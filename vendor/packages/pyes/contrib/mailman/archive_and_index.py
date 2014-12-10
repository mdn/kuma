#!/usr/bin/env python
#
# Copyright (C) 2010 by the Free Software Foundation, Inc.
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301,
# USA.

"""This is a template for constructing an external archiver for situations
where one wants to archive posts in Mailman's pipermail archive, but also
wants to invoke some other process on the archived message after its URL
and/or path are known.

It assumes this is invoked by mm_cfg.py settings like
PUBLIC_EXTERNAL_ARCHIVER = '/path/to/Ext_Arch.py %(hostname)s %(listname)s'
PRIVATE_EXTERNAL_ARCHIVER = '/path/to/Ext_Arch.py %(hostname)s %(listname)s'

The path in the sys.path.insert() below must be adjusted to the actual path
to Mailman's bin/ directory, or you can simply put this script in Mailman's
bin/ directory and it will work without the sys.path.insert() and of course,
you must add the code you want to the ext_process function.
"""

import sys
sys.path.insert(0, '/usr/local/mailman/bin') # path to your mailman dir
import paths

import os
import email
import time

from cStringIO import StringIO

from Mailman import Message
from Mailman import MailList
from Mailman.Archiver import HyperArch
from Mailman.Logging.Syslog import syslog
from Mailman.Logging.Utils import LogStdErr

# For debugging, log stderr to Mailman's 'debug' log
LogStdErr('debug', 'mailmanctl', manual_reprime=0)

def ext_process(listname, hostname, url, filepath, msg):
    """Here's where you put your code to deal with the just archived message.

    Arguments here are the list name, the host name, the URL to the just
    archived message, the file system path to the just archived message and
    the message object.

    These can be replaced or augmented as needed.
    """
    from pyes import ES
    from pyes.exceptions import ClusterBlockException, NoServerAvailable
    import datetime

    #CHANGE this settings to reflect your configuration
    _ES_SERVERS = ['127.0.0.1:9500'] # I prefer thrift
    _indexname = "mailman"
    _doctype = "mail"
    date = datetime.datetime.today()

    try:
        iconn = ES(_ES_SERVERS)
        status = None
        try:
            status = iconn.status(_indexname)
            logger.debug("Indexer status:%s" % status)
        except:
            iconn.create_index(_indexname)
            time.sleep(1)
            status = iconn.status(_indexname)
            mappings = { u'text': {'boost': 1.0,
                                     'index': 'analyzed',
                                     'store': 'yes',
                                     'type': u'string',
                                     "term_vector" : "with_positions_offsets"},
                             u'url': {'boost': 1.0,
                                        'index': 'not_analyzed',
                                        'store': 'yes',
                                        'type': u'string',
                                        "term_vector" : "no"},
                             u'title': {'boost': 1.0,
                                        'index': 'analyzed',
                                        'store': 'yes',
                                        'type': u'string',
                                        "term_vector" : "with_positions_offsets"},
                             u'date': {'store': 'yes',
                                        'type': u'date'}}
            time.sleep(1)
            status = iconn.put_mapping(_doctype, mappings, _indexname)


        data = dict(url=url,
                    title=msg.get('subject'),
                    date=date,
                    text=str(msg)
                    )
        iconn.index(data, _indexname, _doctype)

        syslog('debug', 'listname: %s, hostname: %s, url: %s, path: %s, msg: %s',
               listname, hostname, url, filepath, msg)
    except ClusterBlockException:
        syslog('error', 'Cluster in revocery state: listname: %s, hostname: %s, url: %s, path: %s, msg: %s',
               listname, hostname, url, filepath, msg)
    except NoServerAvailable:
        syslog('error', 'No server available: listname: %s, hostname: %s, url: %s, path: %s, msg: %s',
               listname, hostname, url, filepath, msg)
    except:
        import traceback
        syslog('error', 'Unknown: listname: %s, hostname: %s, url: %s, path: %s, msg: %s\nstacktrace: %s',
               listname, hostname, url, filepath, msg, repr(traceback.format_exc()))

    return

def main():
    """This is the mainline.

    It first invokes the pipermail archiver to add the message to the archive,
    then calls the function above to do whatever with the archived message
    after it's URL and path are known.
    """

    listname = sys.argv[2]
    hostname = sys.argv[1]

    # We must get the list unlocked here because it is already locked in
    # ArchRunner. This is safe because we aren't actually changing our list
    # object. ArchRunner's lock plus pipermail's archive lock will prevent
    # any race conditions.
    mlist = MailList.MailList(listname, lock=False)

    # We need a seekable file for processUnixMailbox()
    f = StringIO(sys.stdin.read())

    # If we don't need a Message.Message instance, we can skip the next and
    # the imports of email and Message above.
    msg = email.message_from_file(f, Message.Message)

    h = HyperArch.HyperArchive(mlist)
    # Get the message number for the next message
    sequence = h.sequence
    # and add the message.
    h.processUnixMailbox(f)
    f.close()

    # Get the archive name, etc.
    archive = h.archive
    msgno = '%06d' % sequence
    filename = msgno + '.html'
    filepath = os.path.join(h.basedir, archive, filename)
    h.close()

    url = '%s%s/%s' % (mlist.GetBaseArchiveURL(), archive, filename)

    ext_process(listname, hostname, url, filepath, msg)

if __name__ == '__main__':
    main()
