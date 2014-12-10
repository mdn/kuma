import datetime

from xml.dom.minidom import parseString

from django.core import mail
from django.core.urlresolvers import reverse
from django.template import Context, Template
from django.test import TestCase
from django.utils.simplejson import loads

from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType

from threadedcomments.models import FreeThreadedComment, ThreadedComment, TestModel
from threadedcomments.models import MARKDOWN, TEXTILE, REST, PLAINTEXT
from threadedcomments.templatetags import threadedcommentstags as tags


__all__ = ("ViewsTestCase",)


class ViewsTestCase(TestCase):
    urls = "threadedcomments.tests.threadedcomments_urls"
    
    def test_freecomment_create(self):
        
        topic = TestModel.objects.create(name="Test2")
        content_type = ContentType.objects.get_for_model(topic)
        
        url = reverse('tc_free_comment', kwargs={
            'content_type': content_type.id,
            'object_id': topic.id
        })
        response = self.client.post(url, {
            'comment': 'test1',
            'name': 'eric',
            'website': 'http://www.eflorenzano.com/',
            'email': 'floguy@gmail.com',
            'next': '/'
        })
        o = FreeThreadedComment.objects.latest('date_submitted').get_base_data(show_dates=False)
        self.assertEquals(o, {
            'website': u'http://www.eflorenzano.com/',
            'comment': u'test1',
            'name': u'eric',
            'parent': None,
            'markup': u'plaintext',
            'content_object': topic,
            'is_public': True,
            'ip_address': u'127.0.0.1',
            'email': u'floguy@gmail.com',
            'is_approved': False
        })
    
    def test_freecomment_preview(self):
        
        topic = TestModel.objects.create(name="Test2")
        content_type = ContentType.objects.get_for_model(topic)
        
        url = reverse('tc_free_comment', kwargs={
            'content_type': content_type.id,
            'object_id': topic.id
        })
        
        response = self.client.post(url, {
            'comment': 'test1',
            'name': 'eric',
            'website': 'http://www.eflorenzano.com/',
            'email': 'floguy@gmail.com',
            'next': '/',
            'preview' : 'True'
        })
        self.assertEquals(len(response.content) > 0, True)
    
    def test_freecomment_edit(self):
        
        topic = TestModel.objects.create(name="Test2")
        
        comment = FreeThreadedComment.objects.create_for_object(topic,
            ip_address = '127.0.0.1',
            comment = "My test free comment!",
        )
        
        url = reverse('tc_free_comment_edit', kwargs={
            'edit_id': comment.pk
        })
        
        response = self.client.post(url, {
            'comment' : 'test1_edited',
            'name' : 'eric',
            'website' : 'http://www.eflorenzano.com/',
            'email' : 'floguy@gmail.com',
            'next' : '/'
        })
        o = FreeThreadedComment.objects.latest('date_submitted').get_base_data(show_dates=False)
        self.assertEquals(o, {
            'website': u'http://www.eflorenzano.com/',
            'comment': u'test1_edited',
            'name': u'eric',
            'parent': None,
            'markup': u'plaintext',
            'content_object': topic,
            'is_public': True,
            'ip_address': u'127.0.0.1',
            'email': u'floguy@gmail.com',
            'is_approved': False
        })
    
    def test_freecomment_edit_with_preview(self):
        
        topic = TestModel.objects.create(name="Test2")
        
        comment = FreeThreadedComment.objects.create_for_object(topic,
            website = "http://oebfare.com/",
            comment = "My test free comment!",
            ip_address = '127.0.0.1',
        )
        
        url = reverse('tc_free_comment_edit', kwargs={
            'edit_id': comment.pk
        })
        
        response = self.client.post(url, {
            'comment': 'test1_edited',
            'name': 'eric',
            'website': 'http://www.eflorenzano.com/',
            'email': 'floguy@gmail.com',
            'next': '/',
            'preview': 'True'
        })
        o = FreeThreadedComment.objects.latest('date_submitted').get_base_data(show_dates=False)
        self.assertEquals(o, {
            'website': u'http://oebfare.com/',
            'comment': u'My test free comment!',
            'name': u'',
            'parent': None,
            'markup': u'plaintext',
            'content_object': topic,
            'is_public': True,
            'ip_address': u'127.0.0.1',
            'email': u'',
            'is_approved': False
        })
        self.assertEquals(len(response.content) > 0, True)
    
    def test_freecomment_json_create(self):
        
        topic = TestModel.objects.create(name="Test2")
        content_type = ContentType.objects.get_for_model(topic)
        
        url = reverse('tc_free_comment_ajax', kwargs={
            'content_type': content_type.id,
            'object_id': topic.id,
            'ajax': 'json'
        })
        
        response = self.client.post(url, {
            'comment': 'test2',
            'name': 'eric',
            'website': 'http://www.eflorenzano.com/',
            'email': 'floguy@gmail.com'
        })
        tmp = loads(response.content)
        o = FreeThreadedComment.objects.latest('date_submitted').get_base_data(show_dates=False)
        self.assertEquals(o, {
            'website': u'http://www.eflorenzano.com/',
            'comment': u'test2',
            'name': u'eric',
            'parent': None,
            'markup': u'plaintext',
            'content_object': topic,
            'is_public': True,
            'ip_address': u'127.0.0.1',
            'email': u'floguy@gmail.com',
            'is_approved': False
        })
    
    def test_freecomment_json_edit(self):
        
        topic = TestModel.objects.create(name="Test2")
        
        comment = FreeThreadedComment.objects.create_for_object(topic,
            ip_address = '127.0.0.1',
            comment = "My test free comment!",
        )
        
        url = reverse('tc_free_comment_edit_ajax',kwargs={
            'edit_id': comment.pk,
            'ajax': 'json'
        })
        
        response = self.client.post(url, {
            'comment': 'test2_edited',
            'name': 'eric',
            'website': 'http://www.eflorenzano.com/',
            'email': 'floguy@gmail.com'
        })
        tmp = loads(response.content)
        o = FreeThreadedComment.objects.latest('date_submitted').get_base_data(show_dates=False)
        self.assertEquals(o, {
            'website': u'http://www.eflorenzano.com/',
            'comment': u'test2_edited',
            'name': u'eric',
            'parent': None,
            'markup': u'plaintext',
            'content_object': topic,
            'is_public': True,
            'ip_address': u'127.0.0.1',
            'email': u'floguy@gmail.com',
            'is_approved': False
        })
    
    def test_freecomment_xml_create(self):
        
        topic = TestModel.objects.create(name="Test2")
        content_type = ContentType.objects.get_for_model(topic)
        
        url = reverse('tc_free_comment_ajax', kwargs={
            'content_type': content_type.id,
            'object_id': topic.id,
            'ajax': 'xml'
        })
        
        response = self.client.post(url, {'comment' : 'test3', 'name' : 'eric', 'website' : 'http://www.eflorenzano.com/', 'email' : 'floguy@gmail.com', 'next' : '/'})
        tmp = parseString(response.content)
        o = FreeThreadedComment.objects.latest('date_submitted').get_base_data(show_dates=False)
        self.assertEquals(o, {
            'website': u'http://www.eflorenzano.com/',
            'comment': u'test3',
            'name': u'eric',
            'parent': None,
            'markup': u'plaintext',
            'content_object': topic,
            'is_public': True,
            'ip_address': u'127.0.0.1',
            'email': u'floguy@gmail.com',
            'is_approved': False
        })
    
    def test_freecomment_xml_edit(self):
        
        topic = TestModel.objects.create(name="Test2")
        
        comment = FreeThreadedComment.objects.create_for_object(topic,
            ip_address = '127.0.0.1',
            comment = "My test free comment!",
        )
        
        url = reverse('tc_free_comment_edit_ajax', kwargs={
            'edit_id': comment.pk,
            'ajax': 'xml'
        })
        
        response = self.client.post(url, {
            'comment': 'test2_edited',
            'name': 'eric',
            'website': 'http://www.eflorenzano.com/',
            'email': 'floguy@gmail.com'
        })
        tmp = parseString(response.content)
        o = FreeThreadedComment.objects.latest('date_submitted').get_base_data(show_dates=False)
        self.assertEquals(o, {
            'website': u'http://www.eflorenzano.com/',
            'comment': u'test2_edited',
            'name': u'eric',
            'parent': None,
            'markup': u'plaintext',
            'content_object': topic,
            'is_public': True,
            'ip_address': u'127.0.0.1',
            'email': u'floguy@gmail.com',
            'is_approved': False
        })
    
    def test_freecomment_child_create(self):
        
        topic = TestModel.objects.create(name="Test2")
        content_type = ContentType.objects.get_for_model(topic)
        
        parent = FreeThreadedComment.objects.create_for_object(topic,
            ip_address = '127.0.0.1',
            comment = "My test free comment!",
        )
        
        url = reverse('tc_free_comment_parent', kwargs={
            'content_type': content_type.id,
            'object_id': topic.id,
            'parent_id': parent.id
        })
        response = self.client.post(url, {
            'comment': 'test4',
            'name': 'eric',
            'website': 'http://www.eflorenzano.com/',
            'email': 'floguy@gmail.com',
            'next' : '/'
        })
        o = FreeThreadedComment.objects.latest('date_submitted').get_base_data(show_dates=False)
        self.assertEquals(o, {
            'website': u'http://www.eflorenzano.com/',
            'comment': u'test4',
            'name': u'eric',
            'parent': parent,
            'markup': u'plaintext',
            'content_object': topic,
            'is_public': True,
            'ip_address': u'127.0.0.1',
            'email': u'floguy@gmail.com',
            'is_approved': False
        })
    
    def test_freecomment_child_json_create(self):
        
        topic = TestModel.objects.create(name="Test2")
        content_type = ContentType.objects.get_for_model(topic)
        
        parent = FreeThreadedComment.objects.create_for_object(topic,
            ip_address = '127.0.0.1',
            comment = "My test free comment!",
        )
        
        url = reverse('tc_free_comment_parent_ajax', kwargs={
            'content_type': content_type.id,
            'object_id': topic.id, 
            'parent_id': parent.id,
            'ajax': 'json'
        })
        
        response = self.client.post(url, {
            'comment': 'test5',
            'name': 'eric',
            'website': 'http://www.eflorenzano.com/',
            'email': 'floguy@gmail.com'
        })
        tmp = loads(response.content)
        o = FreeThreadedComment.objects.latest('date_submitted').get_base_data(show_dates=False)
        self.assertEquals(o, {
            'website': u'http://www.eflorenzano.com/',
            'comment': u'test5',
            'name': u'eric',
            'parent': parent,
            'markup': u'plaintext',
            'content_object': topic,
            'is_public': True,
            'ip_address': u'127.0.0.1',
            'email': u'floguy@gmail.com',
            'is_approved': False
        })
    
    def test_freecomment_child_xml_create(self):
        
        topic = TestModel.objects.create(name="Test2")
        content_type = ContentType.objects.get_for_model(topic)
        
        parent = FreeThreadedComment.objects.create_for_object(topic,
            ip_address = '127.0.0.1',
            comment = "My test free comment!",
        )
        
        url = reverse('tc_free_comment_parent_ajax', kwargs={
            'content_type': content_type.id,
            'object_id': topic.id, 
            'parent_id': parent.id,
            'ajax': 'xml'
        })
        
        response = self.client.post(url, {
            'comment': 'test6', 'name': 'eric',
            'website': 'http://www.eflorenzano.com/',
            'email': 'floguy@gmail.com'
        })
        tmp = parseString(response.content)
        o = FreeThreadedComment.objects.latest('date_submitted').get_base_data(show_dates=False)
        self.assertEquals(o, {
            'website': u'http://www.eflorenzano.com/',
            'comment': u'test6',
            'name': u'eric',
            'parent': parent,
            'markup': u'plaintext',
            'content_object': topic,
            'is_public': True,
            'ip_address': u'127.0.0.1',
            'email': u'floguy@gmail.com',
            'is_approved': False
        })
    
    def create_user_and_login(self):
        user = User.objects.create_user(
            'testuser',
            'testuser@gmail.com',
            'password',
        )
        user.is_active = True
        user.save()
        self.client.login(username='testuser', password='password')
        return user
    
    def test_comment_create(self):
        
        user = self.create_user_and_login()
        
        topic = TestModel.objects.create(name="Test2")
        content_type = ContentType.objects.get_for_model(topic)
        
        url = reverse('tc_comment', kwargs={
            'content_type': content_type.id,
            'object_id': topic.id
        })
        
        response = self.client.post(url, {
            'comment': 'test7',
            'next' : '/'
        })
        o = ThreadedComment.objects.latest('date_submitted').get_base_data(show_dates=False)
        self.assertEquals(o, {
            'comment': u'test7',
            'is_approved': False,
            'parent': None,
            'markup': u'plaintext',
            'content_object': topic,
            'user': user,
            'is_public': True,
            'ip_address': u'127.0.0.1',
        })
    
    def test_comment_preview(self):
        
        user = self.create_user_and_login()
        
        topic = TestModel.objects.create(name="Test2")
        content_type = ContentType.objects.get_for_model(topic)
        
        url = reverse('tc_comment', kwargs={
            'content_type': content_type.id,
            'object_id': topic.id
        })
        
        response = self.client.post(url, {
            'comment': 'test7',
            'next' : '/',
            'preview': 'True'
        })
        self.assertEquals(len(response.content) > 0, True)
    
    def test_comment_edit(self):
        
        user = self.create_user_and_login()
        
        topic = TestModel.objects.create(name="Test2")
        comment = ThreadedComment.objects.create_for_object(topic,
            user = user,
            ip_address = u'127.0.0.1',
            comment = "My test comment!",
        )
        
        url = reverse('tc_comment_edit', kwargs={
            'edit_id': comment.pk,
        })
        
        response = self.client.post(url, {
            'comment': 'test7_edited',
            'next' : '/',
        })
        o = ThreadedComment.objects.latest('date_submitted').get_base_data(show_dates=False)
        self.assertEquals(o, {
            'comment': u'test7_edited',
            'is_approved': False,
            'parent': None,
            'markup': u'plaintext',
            'content_object': topic,
            'user': user,
            'is_public': True,
            'ip_address': u'127.0.0.1',
        })
    
    def test_comment_edit_with_preview(self):
        
        user = self.create_user_and_login()
        
        topic = TestModel.objects.create(name="Test2")
        comment = ThreadedComment.objects.create_for_object(topic,
            user = user,
            ip_address = u'127.0.0.1',
            comment = "My test comment!",
        )
        
        url = reverse('tc_comment_edit', kwargs={
            'edit_id': comment.pk,
        })
        
        response = self.client.post(url, {
            'comment': 'test7_edited',
            'next': '/',
            'preview': 'True'
        })
        
        self.assertEquals(len(response.content) > 0, True)
        o = ThreadedComment.objects.latest('date_submitted').get_base_data(show_dates=False)
        self.assertEquals(o, {
            'comment': u'My test comment!',
            'is_approved': False,
            'parent': None,
            'markup': u'plaintext',
            'content_object': topic,
            'user': user,
            'is_public': True,
            'ip_address': u'127.0.0.1',
        })
    
    def test_comment_json_create(self):
        
        user = self.create_user_and_login()
        
        topic = TestModel.objects.create(name="Test2")
        content_type = ContentType.objects.get_for_model(topic)
        
        url = reverse('tc_comment_ajax', kwargs={
            'content_type': content_type.id,
            'object_id': topic.id,
            'ajax': 'json'
        })
        
        response = self.client.post(url, {
            'comment': 'test8'
        })
        tmp = loads(response.content)
        o = ThreadedComment.objects.latest('date_submitted').get_base_data(show_dates=False)
        self.assertEquals(o, {
            'comment': u'test8',
            'is_approved': False,
            'parent': None,
            'markup': u'plaintext',
            'content_object': topic,
            'user': user,
            'is_public': True,
            'ip_address': u'127.0.0.1',
        })
    
    def test_comment_json_edit(self):
        
        user = self.create_user_and_login()
        
        topic = TestModel.objects.create(name="Test2")
        comment = ThreadedComment.objects.create_for_object(topic,
            user = user,
            ip_address = u'127.0.0.1',
            comment = "My test comment!",
        )
        
        url = reverse('tc_comment_edit_ajax', kwargs={
            'edit_id': comment.pk,
            'ajax': 'json',
        })
        
        response = self.client.post(url, {
            'comment': 'test8_edited'
        })
        tmp = loads(response.content)
        o = ThreadedComment.objects.latest('date_submitted').get_base_data(show_dates=False)
        self.assertEquals(o, {
            'comment': u'test8_edited',
            'is_approved': False,
            'parent': None,
            'markup': u'plaintext',
            'content_object': topic,
            'user': user,
            'is_public': True,
            'ip_address': u'127.0.0.1',
        })
    
    def test_comment_xml_create(self):
        
        user = self.create_user_and_login()
        
        topic = TestModel.objects.create(name="Test2")
        content_type = ContentType.objects.get_for_model(topic)
        
        url = reverse('tc_comment_ajax', kwargs={
            'content_type': content_type.id,
            'object_id': topic.id,
            'ajax': 'xml'
        })
        
        response = self.client.post(url, {
            'comment': 'test9'
        })
        tmp = parseString(response.content)
        o = ThreadedComment.objects.latest('date_submitted').get_base_data(show_dates=False)
        self.assertEquals(o, {
            'comment': u'test9',
            'is_approved': False,
            'parent': None,
            'markup': u'plaintext',
            'content_object': topic,
            'user': user,
            'is_public': True,
            'ip_address': u'127.0.0.1',
        })
    
    def test_comment_xml_edit(self):
        
        user = self.create_user_and_login()
        
        topic = TestModel.objects.create(name="Test2")
        comment = ThreadedComment.objects.create_for_object(topic,
            user = user,
            ip_address = u'127.0.0.1',
            comment = "My test comment!",
        )
        
        url = reverse('tc_comment_edit_ajax', kwargs={
            'edit_id': comment.pk,
            'ajax': 'xml',
        })
        
        response = self.client.post(url, {
            'comment': 'test8_edited'
        })
        tmp = parseString(response.content)
        o = ThreadedComment.objects.latest('date_submitted').get_base_data(show_dates=False)
        self.assertEquals(o, {
            'comment': u'test8_edited',
            'is_approved': False,
            'parent': None,
            'markup': u'plaintext',
            'content_object': topic,
            'user': user,
            'is_public': True,
            'ip_address': u'127.0.0.1',
        })
    
    def test_comment_child_create(self):
        
        user = self.create_user_and_login()
        
        topic = TestModel.objects.create(name="Test2")
        content_type = ContentType.objects.get_for_model(topic)
        
        parent = ThreadedComment.objects.create_for_object(topic,
            user = user,
            ip_address = u'127.0.0.1',
            comment = "My test comment!",
        )
        
        url = reverse('tc_comment_parent', kwargs={
            'content_type': content_type.id,
            'object_id': topic.id,
            'parent_id': parent.id
        })
        
        response = self.client.post(url, {
            'comment': 'test10',
            'next' : '/'
        })
        o = ThreadedComment.objects.latest('date_submitted').get_base_data(show_dates=False)
        self.assertEquals(o, {
            'comment': u'test10',
            'is_approved': False,
            'parent': parent,
            'markup': u'plaintext',
            'content_object': topic,
            'user': user,
            'is_public': True,
            'ip_address': u'127.0.0.1',
        })
    
    def test_comment_child_json_create(self):
        
        user = self.create_user_and_login()
        
        topic = TestModel.objects.create(name="Test2")
        content_type = ContentType.objects.get_for_model(topic)
        
        parent = ThreadedComment.objects.create_for_object(topic,
            user = user,
            ip_address = u'127.0.0.1',
            comment = "My test comment!",
        )
        
        url = reverse('tc_comment_parent_ajax', kwargs={
            'content_type': content_type.id,
            'object_id': topic.id, 
            'parent_id': parent.id,
            'ajax' : 'json'
        })
        
        response = self.client.post(url, {
            'comment' : 'test11'
        })
        tmp = loads(response.content)
        o = ThreadedComment.objects.latest('date_submitted').get_base_data(show_dates=False)
        self.assertEquals(o, {
            'comment': u'test11',
            'is_approved': False,
            'parent': parent,
            'markup': u'plaintext',
            'content_object': topic,
            'user': user,
            'is_public': True,
            'ip_address': u'127.0.0.1',
        })
    
    def test_comment_child_xml_create(self):
        
        user = self.create_user_and_login()
        
        topic = TestModel.objects.create(name="Test2")
        content_type = ContentType.objects.get_for_model(topic)
        
        parent = ThreadedComment.objects.create_for_object(topic,
            user = user,
            ip_address = u'127.0.0.1',
            comment = "My test comment!",
        )
        
        url = reverse('tc_comment_parent_ajax', kwargs={
            'content_type': content_type.id,
            'object_id': topic.id,
            'parent_id': parent.id,
            'ajax' : 'xml'
        })
        
        response = self.client.post(url, {
            'comment': 'test12'
        })
        tmp = parseString(response.content)
        o = ThreadedComment.objects.latest('date_submitted').get_base_data(show_dates=False)
        self.assertEquals(o, {
            'comment': u'test12',
            'is_approved': False,
            'parent': parent,
            'markup': u'plaintext',
            'content_object': topic,
            'user': user,
            'is_public': True,
            'ip_address': u'127.0.0.1',
        })
    
    def test_freecomment_delete(self):
        
        user = User.objects.create_user(
            'testuser',
            'testuser@gmail.com',
            'password',
        )
        user.is_active = True
        user.save()
        self.client.login(username='testuser', password='password')
        
        topic = TestModel.objects.create(name="Test2")
        
        comment = FreeThreadedComment.objects.create_for_object(topic,
            ip_address = u'127.0.0.1',
            comment = "My test comment!",
        )
        deleted_id = comment.id
        
        url = reverse('tc_free_comment_delete', kwargs={
            'object_id': comment.id,
        })
        
        response = self.client.post(url, {'next': '/'})
        o = response['Location'].split('?')[-1] == 'next=/freecomment/%d/delete/' % deleted_id
        self.assertEquals(o, True)
        
        # become super user and try deleting comment
        user.is_superuser = True
        user.save()
        
        response = self.client.post(url, {'next': '/'})
        self.assertEquals(response['Location'], 'http://testserver/')
        self.assertRaises(
            FreeThreadedComment.DoesNotExist,
            lambda: FreeThreadedComment.objects.get(id=deleted_id)
        )
        
        # re-create comment
        comment.save()
        
        response = self.client.get(url, {'next' : '/'})
        self.assertEquals(len(response.content) > 0, True)
        
        o = FreeThreadedComment.objects.get(id=deleted_id) != None
        self.assertEquals(o, True)
    
    def test_comment_delete(self):
        
        some_other_guy = User.objects.create_user(
            'some_other_guy',
            'somewhere@overthemoon.com',
            'password1',
        )
        user = User.objects.create_user(
            'testuser',
            'testuser@gmail.com',
            'password',
        )
        user.is_active = True
        user.save()
        self.client.login(username='testuser', password='password')
        
        topic = TestModel.objects.create(name="Test2")
        
        comment = ThreadedComment.objects.create_for_object(topic,
            user = some_other_guy,
            ip_address = u'127.0.0.1',
            comment = "My test comment!",
        )
        deleted_id = comment.id
        
        url = reverse('tc_comment_delete', kwargs={
            'object_id': comment.id,
        })
        response = self.client.post(url, {'next' : '/'})
        self.assertEquals(response['Location'].split('?')[-1], 'next=/comment/%s/delete/' % deleted_id)
        
        user.is_superuser = True
        user.save()
        
        response = self.client.post(url, {'next' : '/'})
        self.assertEquals(response['Location'], 'http://testserver/')
        self.assertRaises(
            ThreadedComment.DoesNotExist,
            lambda: ThreadedComment.objects.get(id=deleted_id)
        )
        
        # re-create comment
        comment.save()
        
        response = self.client.get(url, {'next' : '/'})
        self.assertEquals(len(response.content) > 0, True)
        
        o = ThreadedComment.objects.get(id=deleted_id) != None
        self.assertEquals(o, True)