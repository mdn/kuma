# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import DataMigration
from django.db import models

class Migration(DataMigration):

    def forwards(self, orm):
        """
        Switch the 'disallow_add_attachment' permission to belong to
        the attachments app instead of the wiki app.

        """
        from django.core.exceptions import ObjectDoesNotExist

        wiki_ctype = None
        disallow_permission = None

        ContentType, Permission = (orm['contenttypes.ContentType'],
                                   orm['auth.Permission'])

        """
        For existing environments, we --fake up to 0003 migration. So, the
        migrations don't create ContentType or Permission models. So, we need
        to send the table create signals that create the necessary attachments
        ContentType and Permission objects, and then get the attachments
        ContentType model
        """
        try:
            attachments_ctype = ContentType.objects.get(app_label='attachments',
                                                       model='attachment')
        except ContentType.DoesNotExist:
            db.send_create_signal('attachments', ['AttachmentRevision'])
            db.send_create_signal('attachments', ['Attachment'])
            db.send_create_signal('attachments', ['DocumentAttachment'])
            attachments_ctype = ContentType.objects.get(app_label='attachments',
                                                       model='attachment')

        try:
            # Both of these are in the try/except because they might
            # not exist on an installation created after this
            # application was split from the wiki.
            wiki_ctype = ContentType.objects.get(app_label='wiki',
                                                 model='attachment')
            disallow_permission = Permission.objects.get(content_type=wiki_ctype,
                                                         codename='disallow_add_attachment')
        except ObjectDoesNotExist:
            # If the install was new enough to not have the permission
            # created in the wiki app, do nothing.
            return
        else:
            # There are two ways we could do this. One way is to loop
            # through every User and Group, switching them from the
            # wiki permission to the attachments permission, which
            # requires a lot of DB activity.
            #
            # The other way is to delete the attachments permission,
            # then switch the content_type of the existing wiki
            # permission (the delete is necessary to avoid violating
            # the unique constraint on Permission). That accomplishes
            # the same result (every User/Group which had the
            # permission will still have it) with far fewer queries.
            #
            # TODO: This leaves the wiki attachment ContentType
            # entries in the database, just in case anything lingers
            # that depends on them. They should be removed once it's
            # verified safe to do so.
            Permission.objects.filter(content_type=attachments_ctype,
                                      codename='disallow_add_attachment').delete()
            disallow_permission.content_type = attachments_ctype
            disallow_permission.save()

    def backwards(self, orm):
        raise RuntimeError("Can't undo attachment permission migration.")

    models = {
        'attachments.attachment': {
            'Meta': {'object_name': 'Attachment', 'db_table': "'wiki_attachment'"},
            'current_revision': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'current_rev'", 'null': 'True', 'to': "orm['attachments.AttachmentRevision']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'mindtouch_attachment_id': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'db_index': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'null': 'True', 'db_index': 'True', 'blank': 'True'}),
            'slug': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'})
        },
        'attachments.attachmentrevision': {
            'Meta': {'object_name': 'AttachmentRevision', 'db_table': "'wiki_attachmentrevision'"},
            'attachment': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'revisions'", 'to': "orm['attachments.Attachment']"}),
            'comment': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'created_attachment_revisions'", 'to': "orm['auth.User']"}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'file': ('django.db.models.fields.files.FileField', [], {'max_length': '500'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_approved': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'db_index': 'True'}),
            'is_mindtouch_migration': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True'}),
            'mime_type': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'}),
            'mindtouch_old_id': ('django.db.models.fields.IntegerField', [], {'unique': 'True', 'null': 'True', 'db_index': 'True'}),
            'slug': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'db_index': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'db_index': 'True'})
        },
        'attachments.documentattachment': {
            'Meta': {'object_name': 'DocumentAttachment'},
            'attached_by': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'null': 'True'}),
            'document': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['wiki.Document']"}),
            'file': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['attachments.Attachment']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.TextField', [], {})
        },
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'ordering': "('content_type__app_label', 'content_type__model', 'codename')", 'unique_together': "(('content_type', 'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'teamwork.team': {
            'Meta': {'object_name': 'Team'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'db_index': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'founder': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'null': 'True', 'db_index': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '128', 'db_index': 'True'})
        },
        'tidings.watch': {
            'Meta': {'object_name': 'Watch'},
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']", 'null': 'True', 'blank': 'True'}),
            'email': ('django.db.models.fields.EmailField', [], {'db_index': 'True', 'max_length': '75', 'null': 'True', 'blank': 'True'}),
            'event_type': ('django.db.models.fields.CharField', [], {'max_length': '30', 'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True'}),
            'object_id': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'db_index': 'True'}),
            'secret': ('django.db.models.fields.CharField', [], {'max_length': '10', 'null': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'null': 'True', 'blank': 'True'})
        },
        'wiki.document': {
            'Meta': {'unique_together': "(('parent', 'locale'), ('slug', 'locale'))", 'object_name': 'Document'},
            'body_html': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'category': ('django.db.models.fields.IntegerField', [], {'db_index': 'True'}),
            'current_revision': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'current_for+'", 'null': 'True', 'to': "orm['wiki.Revision']"}),
            'defer_rendering': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True'}),
            'deleted': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True'}),
            'files': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['attachments.Attachment']", 'through': "orm['attachments.DocumentAttachment']", 'symmetrical': 'False'}),
            'html': ('django.db.models.fields.TextField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_localizable': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'db_index': 'True'}),
            'is_redirect': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True'}),
            'is_template': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True'}),
            'json': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'last_rendered_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'db_index': 'True'}),
            'locale': ('sumo.models.LocaleField', [], {'default': "'en-US'", 'max_length': '7', 'db_index': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'null': 'True', 'db_index': 'True', 'blank': 'True'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'translations'", 'null': 'True', 'to': "orm['wiki.Document']"}),
            'parent_topic': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'children'", 'null': 'True', 'to': "orm['wiki.Document']"}),
            'quick_links_html': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'related_documents': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['wiki.Document']", 'through': "orm['wiki.RelatedDocument']", 'symmetrical': 'False'}),
            'render_expires': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'render_max_age': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'render_scheduled_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'db_index': 'True'}),
            'render_started_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'db_index': 'True'}),
            'rendered_errors': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'rendered_html': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'slug': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'}),
            'summary_html': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'summary_text': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'team': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['teamwork.Team']", 'null': 'True', 'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'}),
            'toc_html': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'zone_subnav_local_html': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'})
        },
        'wiki.relateddocument': {
            'Meta': {'ordering': "['-in_common']", 'object_name': 'RelatedDocument'},
            'document': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'related_from'", 'to': "orm['wiki.Document']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'in_common': ('django.db.models.fields.IntegerField', [], {}),
            'related': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'related_to'", 'to': "orm['wiki.Document']"})
        },
        'wiki.revision': {
            'Meta': {'object_name': 'Revision'},
            'based_on': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['wiki.Revision']", 'null': 'True', 'blank': 'True'}),
            'comment': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'content': ('django.db.models.fields.TextField', [], {}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'db_index': 'True'}),
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'created_revisions'", 'to': "orm['auth.User']"}),
            'document': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'revisions'", 'to': "orm['wiki.Document']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_approved': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'db_index': 'True'}),
            'is_mindtouch_migration': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True'}),
            'keywords': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'render_max_age': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'slug': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'db_index': 'True'}),
            'summary': ('django.db.models.fields.TextField', [], {}),
            'tags': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'db_index': 'True'}),
            'toc_depth': ('django.db.models.fields.IntegerField', [], {'default': '1'})
        }
    }

    complete_apps = ['attachments']
    symmetrical = True
