from datetime import timedelta

from kuma.core.tests import eq_, ok_
from kuma.users.tests import UserTestCase, user

from . import revision
from ..jobs import DocumentZoneStackJob, DocumentContributorsJob
from ..models import Document, DocumentZone


class DocumentZoneTests(UserTestCase):
    """Tests for content zones in topic hierarchies"""

    def test_find_roots(self):
        """Ensure sub pages can find the content zone root"""
        root_rev = revision(title='ZoneRoot', slug='ZoneRoot',
                            content='This is the Zone Root',
                            is_approved=True, save=True)
        root_doc = root_rev.document

        middle_rev = revision(title='Zonemiddle', slug='Zonemiddle',
                              content='This is the Zone middle',
                              is_approved=True, save=True)
        middle_doc = middle_rev.document
        middle_doc.parent_topic = root_doc
        middle_doc.save()

        sub_rev = revision(title='SubPage', slug='SubPage',
                           content='This is a subpage',
                           is_approved=True, save=True)
        sub_doc = sub_rev.document
        sub_doc.parent_topic = middle_doc
        sub_doc.save()

        sub_sub_rev = revision(title='SubSubPage', slug='SubSubPage',
                               content='This is a subsubpage',
                               is_approved=True, save=True)
        sub_sub_doc = sub_sub_rev.document
        sub_sub_doc.parent_topic = sub_doc
        sub_sub_doc.save()

        other_rev = revision(title='otherPage', slug='otherPage',
                             content='This is an otherpage',
                             is_approved=True, save=True)
        other_doc = other_rev.document

        root_zone = DocumentZone(document=root_doc)
        root_zone.save()

        middle_zone = DocumentZone(document=middle_doc)
        middle_zone.save()

        eq_(self.get_zone_stack(root_doc)[0], root_zone)
        eq_(self.get_zone_stack(middle_doc)[0], middle_zone)
        eq_(self.get_zone_stack(sub_doc)[0], middle_zone)
        eq_(0, len(self.get_zone_stack(other_doc)))

        zone_stack = self.get_zone_stack(sub_sub_doc)
        eq_(zone_stack[0], middle_zone)
        eq_(zone_stack[1], root_zone)

    def get_zone_stack(self, doc):
        return DocumentZoneStackJob().get(doc.pk)


class DocumentContributorsTests(UserTestCase):

    def test_contributors(self):
        contrib = user(save=True)
        rev = revision(creator=contrib, save=True)
        job = DocumentContributorsJob()
        # setting this to true to be able to test this
        job.fetch_on_miss = True
        eq_(contrib.pk, job.get(rev.document.pk)[0]['id'])

    def test_contributors_ordering(self):
        contrib_1 = user(save=True)
        contrib_2 = user(save=True)
        contrib_3 = user(save=True)
        rev_1 = revision(creator=contrib_1, save=True)
        rev_2 = revision(creator=contrib_2,
                         document=rev_1.document,
                         # live in the future to make sure we handle the lack
                         # of microseconds support in Django 1.7 nicely
                         created=rev_1.created + timedelta(seconds=1),
                         save=True)
        ok_(rev_1.created < rev_2.created)
        job = DocumentContributorsJob()
        job_user_pks = [contributor['id']
                        for contributor in job.fetch(rev_1.document.pk)]
        # the user with the more recent revision first
        recent_contributors_pks = [contrib_2.pk, contrib_1.pk]
        eq_(job_user_pks, recent_contributors_pks)

        # a third revision should now show up again and
        # the job's cache is invalidated
        rev_3 = revision(creator=contrib_3,
                         document=rev_1.document,
                         created=rev_2.created + timedelta(seconds=1),
                         save=True)
        ok_(rev_2.created < rev_3.created)
        job_user_pks = [contributor['id']
                        for contributor in job.fetch(rev_1.document.pk)]
        # The new revision shows up
        eq_(job_user_pks, [contrib_3.pk] + recent_contributors_pks)

    def test_contributors_inactive_or_banned(self):
        contrib_1 = user(save=True)
        contrib_2 = user(is_active=False, save=True)
        contrib_3 = user(save=True)
        contrib_3_ban = contrib_3.bans.create(by=contrib_1, reason='because reasons')
        revision_2 = revision(creator=contrib_1, save=True)

        revision(creator=contrib_2, document=revision_2.document, save=True)
        revision(creator=contrib_3, document=revision_2.document, save=True)

        job = DocumentContributorsJob()
        # setting this to true to be able to test this
        job.fetch_on_miss = True

        contributors = job.get(revision_2.document.pk)
        contrib_ids = [contrib['id'] for contrib in contributors]
        self.assertIn(contrib_1.id, contrib_ids)
        self.assertNotIn(contrib_2.id, contrib_ids)
        self.assertNotIn(contrib_3.id, contrib_ids)

        # delete the ban again
        contrib_3_ban.delete()
        # reloading the document from db to prevent cache
        doc = Document.objects.get(pk=revision_2.document.pk)
        # user not in contributors because job invalidation hasn't happened
        contrib_ids = [contrib['id']
                       for contrib in job.get(revision_2.document.pk)]
        self.assertNotIn(contrib_3.id, contrib_ids)

        # trigger the invalidation manually by saving the document
        doc.save()
        doc = Document.objects.get(pk=revision_2.document.pk)
        contrib_ids = [contrib['id']
                       for contrib in job.get(revision_2.document.pk)]
        self.assertIn(contrib_3.id, contrib_ids)
