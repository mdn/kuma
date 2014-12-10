from django.core import mail
from django.test import TestCase

from django.contrib.auth.models import User

from threadedcomments.moderation import moderator, CommentModerator
from threadedcomments.models import FreeThreadedComment, ThreadedComment, TestModel
from threadedcomments.models import MARKDOWN, TEXTILE, REST, PLAINTEXT


__all__ = ("ModeratorTestCase",)


class ModeratorTestCase(TestCase):
    
    def test_threadedcomment(self):
        topic = TestModel.objects.create(name = "Test")
        user = User.objects.create_user('user', 'floguy@gmail.com', password='password')
        user2 = User.objects.create_user('user2', 'floguy@gmail.com', password='password')
        
        comment1 = ThreadedComment.objects.create_for_object(
            topic, user = user, ip_address = '127.0.0.1',
            comment = 'This is fun!  This is very fun!',
        )
        comment2 = ThreadedComment.objects.create_for_object(
            topic, user = user, ip_address = '127.0.0.1',
            comment = 'This is stupid!  I hate it!',
        )
        comment3 = ThreadedComment.objects.create_for_object(
            topic, user = user, ip_address = '127.0.0.1', parent = comment2,
            comment = 'I agree, the first comment was wrong and you are right!',
        )
        comment4 = ThreadedComment.objects.create_for_object(
            topic, user = user, ip_address = '127.0.0.1',
            comment = 'What are we talking about?',
        )
        comment5 = ThreadedComment.objects.create_for_object(
            topic, user = user, ip_address = '127.0.0.1', parent = comment3,
            comment = "I'm a fanboy!",
        )
        comment6 = ThreadedComment.objects.create_for_object(
            topic, user = user, ip_address = '127.0.0.1', parent = comment1,
            comment = "What are you talking about?",
        )
        
        class Moderator1(CommentModerator):
            enable_field = 'is_public'
            auto_close_field = 'date'
            close_after = 15
        moderator.register(TestModel, Moderator1)
        
        comment7 = ThreadedComment.objects.create_for_object(
            topic, user = user, ip_address = '127.0.0.1',
            comment = "Post moderator addition.  Does it still work?",
        )
        
        topic.is_public = False
        topic.save()
        
        comment8 = ThreadedComment.objects.create_for_object(
            topic, user = user, ip_address = '127.0.0.1', parent = comment7,
            comment = "This should not appear, due to enable_field",
        )
        
        moderator.unregister(TestModel)
        
        comment9 = ThreadedComment.objects.create_for_object(
            topic, user = user, ip_address = '127.0.0.1',
            comment = "This should appear again, due to unregistration",
        )

        self.assertEquals(len(mail.outbox), 0)
        
        ##################
        
        class Moderator2(CommentModerator):
            enable_field = 'is_public'
            auto_close_field = 'date'
            close_after = 15
            akismet = False
            email_notification = True
        moderator.register(TestModel, Moderator2)
        
        comment10 = ThreadedComment.objects.create_for_object(
            topic, user = user, ip_address = '127.0.0.1',
            comment = "This should not appear again, due to registration with a new manager.",
        )
        
        topic.is_public = True
        topic.save()
        
        comment11 = ThreadedComment.objects.create_for_object(
            topic, user = user, ip_address = '127.0.0.1', parent = comment1,
            comment = "This should appear again.",
        )
        
        self.assertEquals(len(mail.outbox), 1)
        mail.outbox = []
        
        topic.date = topic.date - datetime.timedelta(days = 20)
        topic.save()
        
        comment12 = ThreadedComment.objects.create_for_object(
            topic, user = user, ip_address = '127.0.0.1', parent = comment7,
            comment = "This shouldn't appear, due to close_after=15.",
        )
        
        topic.date = topic.date + datetime.timedelta(days = 20)
        topic.save()
        
        moderator.unregister(TestModel)
        
        class Moderator3(CommentModerator):
            max_comment_length = 10
        moderator.register(TestModel, Moderator3)
        
        comment13 = ThreadedComment.objects.create_for_object(
            topic, user = user, ip_address = '127.0.0.1', parent = comment7,
            comment = "This shouldn't appear because it has more than 10 chars.",
        )
        
        comment14 = ThreadedComment.objects.create_for_object(
            topic, user = user, ip_address = '127.0.0.1', parent = comment7,
            comment = "<10chars",
        )
        
        moderator.unregister(TestModel)
        
        class Moderator4(CommentModerator):
            allowed_markup = [REST,]
        moderator.register(TestModel, Moderator4)
        
        comment15 = ThreadedComment.objects.create_for_object(
            topic, user = user, ip_address = '127.0.0.1', parent = comment7,
            comment = "INVALID Markup.  Should not show up.", markup=TEXTILE
        )
        
        comment16 = ThreadedComment.objects.create_for_object(
            topic, user = user, ip_address = '127.0.0.1', parent = comment7,
            comment = "VALID Markup.  Should show up.", markup=REST
        )
        
        moderator.unregister(TestModel)
        
        tree = ThreadedComment.public.get_tree(topic)
        output = []
        for comment in tree:
            output.append("%s %s" % ("    " * comment.depth, comment.comment))
        self.assertEquals("\n".join(output),
"""
This is fun!  This is very fun!
    What are you talking about?
    This should appear again.
This is stupid!  I hate it!
    I agree, the first comment was wrong and you are right!
        I'm a fanboy!
What are we talking about?
Post moderator addition.  Does it still work?
    <10chars
    VALID Markup.  Should show up.
This should appear again, due to unregistration
""".lstrip())

        tree = ThreadedComment.objects.get_tree(topic)
        output = []
        for comment in tree:
            output.append("%s %s" % ("    " * comment.depth, comment.comment))
        self.assertEquals("\n".join(output),
"""
This is fun!  This is very fun!
    What are you talking about?
    This should appear again.
This is stupid!  I hate it!
    I agree, the first comment was wrong and you are right!
        I'm a fanboy!
What are we talking about?
Post moderator addition.  Does it still work?
    This shouldn't appear because it has more than 10 chars.
    <10chars
    VALID Markup.  Should show up.
This should appear again, due to unregistration
""".lstrip())
        
        tree = ThreadedComment.objects.get_tree(topic, root=comment2)
        output = []
        for comment in tree:
            output.append("%s %s" % ("    " * comment.depth, comment.comment))
        self.assertEquals("\n".join(output),
"""
This is stupid!  I hate it!
    I agree, the first comment was wrong and you are right!
        I'm a fanboy!
""".lstrip())
        
        tree = ThreadedComment.objects.get_tree(topic, root=comment2.id)
        for comment in tree:
            output.append("%s %s" % ("    " * comment.depth, comment.comment))
        self.assertEquals("\n".join(output),
"""
This is stupid!  I hate it!
    I agree, the first comment was wrong and you are right!
        I'm a fanboy!
""".lstrip())
        
    def test_freethreadedcomment(self):
        
        ###########################
        ### FreeThreadedComment ###
        ###########################
        
        fcomment1 = FreeThreadedComment.objects.create_for_object(
            topic, name = "Eric", ip_address = '127.0.0.1',
            comment = 'This is fun!  This is very fun!',
        )
        fcomment2 = FreeThreadedComment.objects.create_for_object(
            topic, name = "Eric", ip_address = '127.0.0.1',
            comment = 'This is stupid!  I hate it!',
        )
        fcomment3 = FreeThreadedComment.objects.create_for_object(
            topic, name = "Eric", ip_address = '127.0.0.1', parent = fcomment2,
            comment = 'I agree, the first comment was wrong and you are right!',
        )
        fcomment4 = FreeThreadedComment.objects.create_for_object(
            topic, name = "Eric", ip_address = '127.0.0.1', 
            website="http://www.eflorenzano.com/", email="floguy@gmail.com",
            comment = 'What are we talking about?',
        )
        fcomment5 = FreeThreadedComment.objects.create_for_object(
            topic, name = "Eric", ip_address = '127.0.0.1', parent = fcomment3,
            comment = "I'm a fanboy!",
        )
        fcomment6 = FreeThreadedComment.objects.create_for_object(
            topic, name = "Eric", ip_address = '127.0.0.1', parent = fcomment1,
            comment = "What are you talking about?",
        )
        
        moderator.register(TestModel, Moderator1)
        
        fcomment7 = FreeThreadedComment.objects.create_for_object(
            topic, name = "Eric", ip_address = '127.0.0.1',
            comment = "Post moderator addition.  Does it still work?",
        )
        
        topic.is_public = False
        topic.save()
        
        fcomment8 = FreeThreadedComment.objects.create_for_object(
            topic, name = "Eric", ip_address = '127.0.0.1', parent = fcomment7,
            comment = "This should not appear, due to enable_field",
        )
        
        moderator.unregister(TestModel)
        
        fcomment9 = FreeThreadedComment.objects.create_for_object(
            topic, name = "Eric", ip_address = '127.0.0.1',
            comment = "This should appear again, due to unregistration",
        )
        
        self.assertEquals(len(mail.outbox), 0)

        moderator.register(TestModel, Moderator2)
        
        fcomment10 = FreeThreadedComment.objects.create_for_object(
            topic, name = "Eric", ip_address = '127.0.0.1',
            comment = "This should not appear again, due to registration with a new manager.",
        )
        
        topic.is_public = True
        topic.save()
        
        fcomment11 = FreeThreadedComment.objects.create_for_object(
            topic, name = "Eric", ip_address = '127.0.0.1', parent = fcomment1,
            comment = "This should appear again.",
        )
        
        self.assertEquals(len(mail.outbox), 1)
        
        mail.outbox = []
        
        topic.date = topic.date - datetime.timedelta(days = 20)
        topic.save()
        
        fcomment12 = FreeThreadedComment.objects.create_for_object(
            topic, name = "Eric", ip_address = '127.0.0.1', parent = fcomment7,
            comment = "This shouldn't appear, due to close_after=15.",
        )
        
        topic.date = topic.date + datetime.timedelta(days = 20)
        topic.save()
        
        moderator.unregister(TestModel)
        moderator.register(TestModel, Moderator3)
        
        fcomment13 = FreeThreadedComment.objects.create_for_object(
            topic, name = "Eric", ip_address = '127.0.0.1', parent = fcomment7,
            comment = "This shouldn't appear because it has more than 10 chars.",
        )
        
        fcomment14 = FreeThreadedComment.objects.create_for_object(
            topic, name = "Eric", ip_address = '127.0.0.1', parent = fcomment7,
            comment = "<10chars",
        )
        
        moderator.unregister(TestModel)
        class Moderator5(CommentModerator):
            allowed_markup = [REST,]
            max_depth = 3
        moderator.register(TestModel, Moderator5)
        
        fcomment15 = FreeThreadedComment.objects.create_for_object(
            topic, name = "Eric", ip_address = '127.0.0.1', parent = fcomment7,
            comment = "INVALID Markup.  Should not show up.", markup=TEXTILE
        )
        
        fcomment16 = FreeThreadedComment.objects.create_for_object(
            topic, name = "Eric", ip_address = '127.0.0.1', parent = None,
            comment = "VALID Markup.  Should show up.", markup=REST
        )
        
        fcomment17 = FreeThreadedComment.objects.create_for_object(
            topic, name = "Eric", ip_address = '127.0.0.1', parent = fcomment16,
            comment = "Building Depth...Should Show Up.", markup=REST
        )
        
        fcomment18 = FreeThreadedComment.objects.create_for_object(
            topic, name = "Eric", ip_address = '127.0.0.1', parent = fcomment17,
            comment = "More Depth...Should Show Up.", markup=REST
        )
        
        fcomment19 = FreeThreadedComment.objects.create_for_object(
            topic, name = "Eric", ip_address = '127.0.0.1', parent = fcomment18,
            comment = "Too Deep..Should NOT Show UP", markup=REST
        )
        
        moderator.unregister(TestModel)
        
        tree = FreeThreadedComment.public.get_tree(topic)
        output = []
        for comment in tree:
            output.append("%s %s" % ("    " * comment.depth, comment.comment))
        self.assertEquals("\n".join(output),
"""
This is fun!  This is very fun!
    What are you talking about?
    This should appear again.
This is stupid!  I hate it!
    I agree, the first comment was wrong and you are right!
        I'm a fanboy!
What are we talking about?
Post moderator addition.  Does it still work?
    <10chars
This should appear again, due to unregistration
VALID Markup.  Should show up.
    Building Depth...Should Show Up.
        More Depth...Should Show Up.
""".lstrip())
        
        tree = FreeThreadedComment.objects.get_tree(topic)
        output = []
        for comment in tree:
            output.append("%s %s" % ("    " * comment.depth, comment.comment))
        self.assertEquals("\n".join(output),
"""
This is fun!  This is very fun!
    What are you talking about?
    This should appear again.
This is stupid!  I hate it!
    I agree, the first comment was wrong and you are right!
        I'm a fanboy!
What are we talking about?
Post moderator addition.  Does it still work?
    This shouldn't appear because it has more than 10 chars.
    <10chars
This should appear again, due to unregistration
VALID Markup.  Should show up.
    Building Depth...Should Show Up.
        More Depth...Should Show Up.
""".lstrip())
        
        tree = FreeThreadedComment.objects.get_tree(topic, root=comment2)
        output = []
        for comment in tree:
            output.append("%s %s" % ("    " * comment.depth, comment.comment))
        self.assertEquals("\n".join(output),
"""
This is stupid!  I hate it!
    I agree, the first comment was wrong and you are right!
        I'm a fanboy!
""".lstrip())
        
        tree = FreeThreadedComment.objects.get_tree(topic, root=comment2.id)
        output = []
        for comment in tree:
            output.append("%s %s" % ("    " * comment.depth, comment.comment))
        self.assertEquals("\n".join(output),
"""
This is stupid!  I hate it!
    I agree, the first comment was wrong and you are right!
        I'm a fanboy!
""".lstrip())
