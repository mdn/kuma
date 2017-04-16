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


__all__ = ("TemplateTagTestCase",)


class TemplateTagTestCase(TestCase):
    urls = "threadedcomments.tests.threadedcomments_urls"
    
    def test_get_comment_url(self):
        
        user = User.objects.create_user('user', 'floguy@gmail.com', password='password')
        
        topic = TestModel.objects.create(name="Test2")
        content_type = ContentType.objects.get_for_model(topic)
        
        comment = ThreadedComment.objects.create_for_object(topic,
            user = user,
            ip_address = '127.0.0.1',
            comment = "My test comment!",
        )
        
        c = Context({
            'topic': topic,
            'parent': comment
        })
        sc = {
            "ct": content_type.pk,
            "id": topic.pk,
            "pid": comment.pk,
        }
        
        self.assertEquals(Template('{% load threadedcommentstags %}{% get_comment_url topic %}').render(c), u'/comment/%(ct)s/%(id)s/' % sc)
        self.assertEquals(Template('{% load threadedcommentstags %}{% get_comment_url topic parent %}').render(c), u'/comment/%(ct)s/%(id)s/%(pid)s/' % sc)
        self.assertEquals(Template('{% load threadedcommentstags %}{% get_comment_url_json topic %}').render(c), u'/comment/%(ct)s/%(id)s/json/' % sc)
        self.assertEquals(Template('{% load threadedcommentstags %}{% get_comment_url_xml topic %}').render(c), u'/comment/%(ct)s/%(id)s/xml/' % sc)
        self.assertEquals(Template('{% load threadedcommentstags %}{% get_comment_url_json topic parent %}').render(c), u'/comment/%(ct)s/%(id)s/%(pid)s/json/' % sc)
        self.assertEquals(Template('{% load threadedcommentstags %}{% get_comment_url_xml topic parent %}').render(c), u'/comment/%(ct)s/%(id)s/%(pid)s/xml/' % sc)
    
    def test_get_free_comment_url(self):
        
        topic = TestModel.objects.create(name="Test2")
        content_type = ContentType.objects.get_for_model(topic)
        
        comment = FreeThreadedComment.objects.create_for_object(topic,
            ip_address = '127.0.0.1',
            comment = "My test free comment!",
        )
        
        c = Context({
            'topic': topic,
            'parent': comment,
        })
        sc = {
            "ct": content_type.pk,
            "id": topic.pk,
            "pid": comment.pk,
        }
        
        self.assertEquals(Template('{% load threadedcommentstags %}{% get_free_comment_url topic %}').render(c), u'/freecomment/%(ct)s/%(id)s/' % sc)
        self.assertEquals(Template('{% load threadedcommentstags %}{% get_free_comment_url topic parent %}').render(c), u'/freecomment/%(ct)s/%(id)s/%(pid)s/' % sc)
        self.assertEquals(Template('{% load threadedcommentstags %}{% get_free_comment_url_json topic %}').render(c), u'/freecomment/%(ct)s/%(id)s/json/' % sc)
        self.assertEquals(Template('{% load threadedcommentstags %}{% get_free_comment_url_xml topic %}').render(c), u'/freecomment/%(ct)s/%(id)s/xml/' % sc)
        self.assertEquals(Template('{% load threadedcommentstags %}{% get_free_comment_url_json topic parent %}').render(c), u'/freecomment/%(ct)s/%(id)s/%(pid)s/json/' % sc)
        self.assertEquals(Template('{% load threadedcommentstags %}{% get_free_comment_url_xml topic parent %}').render(c), u'/freecomment/%(ct)s/%(id)s/%(pid)s/xml/' % sc)
    
    def test_get_comment_count(self):
        
        user = User.objects.create_user('user', 'floguy@gmail.com', password='password')
        
        topic = TestModel.objects.create(name="Test2")
        
        comment = ThreadedComment.objects.create_for_object(topic,
            user = user,
            ip_address = '127.0.0.1',
            comment = "My test comment!",
        )
        
        c = Context({
            'topic': topic,
        })
        
        self.assertEquals(
            Template('{% load threadedcommentstags %}{% get_comment_count for topic as count %}{{ count }}').render(c),
            u'1'
        )
    
    def test_get_free_comment_count(self):
        
        topic = TestModel.objects.create(name="Test2")
        
        comment = FreeThreadedComment.objects.create_for_object(topic,
            ip_address = '127.0.0.1',
            comment = "My test free comment!",
        )
        
        c = Context({
            'topic': topic,
        })
        
        self.assertEquals(
            Template('{% load threadedcommentstags %}{% get_free_comment_count for topic as count %}{{ count }}').render(c),
            u'1'
        )
    
    def test_get_threaded_comment_form(self):
        self.assertEquals(
            Template('{% load threadedcommentstags %}{% get_threaded_comment_form as form %}{{ form }}').render(Context({})),
            u'<tr><th><label for="id_comment">comment:</label></th><td><textarea id="id_comment" rows="10" cols="40" name="comment"></textarea></td></tr>\n<tr><th><label for="id_markup">Markup:</label></th><td><select name="markup" id="id_markup">\n<option value="">---------</option>\n<option value="1">markdown</option>\n<option value="2">textile</option>\n<option value="3">restructuredtext</option>\n<option value="5" selected="selected">plaintext</option>\n</select></td></tr>'
        )
    
    def test_get_latest_comments(self):
        
        user = User.objects.create_user('user', 'floguy@gmail.com', password='password')
        
        topic = TestModel.objects.create(name="Test2")
        old_topic = topic
        content_type = ContentType.objects.get_for_model(topic)
        
        ThreadedComment.objects.create_for_object(topic,
            user = user,
            ip_address = '127.0.0.1',
            comment = "Test 1",
        )
        ThreadedComment.objects.create_for_object(topic,
            user = user,
            ip_address = '127.0.0.1',
            comment = "Test 2",
        )
        ThreadedComment.objects.create_for_object(topic,
            user = user,
            ip_address = '127.0.0.1',
            comment = "Test 3",
        )
        
        self.assertEquals(
            Template('{% load threadedcommentstags %}{% get_latest_comments 2 as comments %}{{ comments }}').render(Context({})),
            u'[&lt;ThreadedComment: Test 3&gt;, &lt;ThreadedComment: Test 2&gt;]'
        )
    
    def test_get_latest_free_comments(self):
        
        topic = TestModel.objects.create(name="Test2")
        
        FreeThreadedComment.objects.create_for_object(topic,
            ip_address = '127.0.0.1',
            comment = "Test 1",
        )
        FreeThreadedComment.objects.create_for_object(topic,
            ip_address = '127.0.0.1',
            comment = "Test 2",
        )
        FreeThreadedComment.objects.create_for_object(topic,
            ip_address = '127.0.0.1',
            comment = "Test 3",
        )
        
        self.assertEquals(
            Template('{% load threadedcommentstags %}{% get_latest_free_comments 2 as comments %}{{ comments }}').render(Context({})),
            u'[&lt;FreeThreadedComment: Test 3&gt;, &lt;FreeThreadedComment: Test 2&gt;]'
        )
    
    def test_get_threaded_comment_tree(self):
        
        user = User.objects.create_user('user', 'floguy@gmail.com', password='password')
        
        topic = TestModel.objects.create(name="Test2")
        
        parent1 = ThreadedComment.objects.create_for_object(topic,
            user = user,
            ip_address = '127.0.0.1',
            comment = "test1",
        )
        ThreadedComment.objects.create_for_object(topic,
            user = user,
            ip_address = '127.0.0.1',
            comment = "test2",
            parent = parent1,
        )
        parent2 = ThreadedComment.objects.create_for_object(topic,
            user = user,
            ip_address = '127.0.0.1',
            comment = "test3",
        )
        ThreadedComment.objects.create_for_object(topic,
            user = user,
            ip_address = '127.0.0.1',
            comment = "test4",
            parent = parent2,
        )
        
        c = Context({
            'topic': topic,
        })
        
        self.assertEquals(
            Template('{% load threadedcommentstags %}{% get_threaded_comment_tree for topic as tree %}[{% for item in tree %}({{ item.depth }}){{ item.comment }},{% endfor %}]').render(c),
            u'[(0)test1,(1)test2,(0)test3,(1)test4,]'
        )
        self.assertEquals(
            Template('{% load threadedcommentstags %}{% get_threaded_comment_tree for topic 3 as tree %}[{% for item in tree %}({{ item.depth }}){{ item.comment }},{% endfor %}]').render(c),
            u'[(0)test3,(1)test4,]'
        )
    
    def test_get_free_threaded_comment_tree(self):
        
        topic = TestModel.objects.create(name="Test2")
        
        parent1 = FreeThreadedComment.objects.create_for_object(topic,
            ip_address = '127.0.0.1',
            comment = "test1",
        )
        FreeThreadedComment.objects.create_for_object(topic,
            ip_address = '127.0.0.1',
            comment = "test2",
            parent = parent1,
        )
        parent2 = FreeThreadedComment.objects.create_for_object(topic,
            ip_address = '127.0.0.1',
            comment = "test3",
        )
        FreeThreadedComment.objects.create_for_object(topic,
            ip_address = '127.0.0.1',
            comment = "test4",
            parent = parent2,
        )
        
        c = Context({
            'topic': topic,
        })
        
        self.assertEquals(
            Template('{% load threadedcommentstags %}{% get_free_threaded_comment_tree for topic as tree %}[{% for item in tree %}({{ item.depth }}){{ item.comment }},{% endfor %}]').render(c),
            u'[(0)test1,(1)test2,(0)test3,(1)test4,]'
        )
        self.assertEquals(
            Template('{% load threadedcommentstags %}{% get_free_threaded_comment_tree for topic 3 as tree %}[{% for item in tree %}({{ item.depth }}){{ item.comment }},{% endfor %}]').render(c),
            u'[(0)test3,(1)test4,]'
        )
    
    def test_user_comment_tags(self):
        
        user1 = User.objects.create_user('eric', 'floguy@gmail.com', password='password')
        user2 = User.objects.create_user('brian', 'brosner@gmail.com', password='password')
        
        topic = TestModel.objects.create(name="Test2")
        
        ThreadedComment.objects.create_for_object(topic,
            user = user1,
            ip_address = '127.0.0.1',
            comment = "Eric comment",
        )
        ThreadedComment.objects.create_for_object(topic,
            user = user2,
            ip_address = '127.0.0.1',
            comment = "Brian comment",
        )
        
        c = Context({
            'user': user1,
        })
        
        self.assertEquals(
            Template('{% load threadedcommentstags %}{% get_user_comments for user as comments %}{{ comments }}').render(c),
            u'[&lt;ThreadedComment: Eric comment&gt;]'
        )
        self.assertEquals(
            Template('{% load threadedcommentstags %}{% get_user_comment_count for user as comment_count %}{{ comment_count }}').render(c),
            u'1',
        )
    
    def test_markdown_comment(self):
        
        user = User.objects.create_user('user', 'floguy@gmail.com', password='password')
        topic = TestModel.objects.create(name="Test2")
        
        markdown_txt = '''
A First Level Header
====================

A Second Level Header
---------------------

Now is the time for all good men to come to
the aid of their country. This is just a
regular paragraph.

The quick brown fox jumped over the lazy
dog's back.

### Header 3

> This is a blockquote.
> 
> This is the second paragraph in the blockquote.
>
> ## This is an H2 in a blockquote
'''

        comment_markdown = ThreadedComment.objects.create_for_object(
            topic, user = user, ip_address = '127.0.0.1', markup = MARKDOWN,
            comment = markdown_txt,
        )

        c = Context({
            'comment': comment_markdown,
        })
        s = Template("{% load threadedcommentstags %}{% auto_transform_markup comment %}").render(c).replace('\\n', '')
        self.assertEquals(s.startswith(u"<h1>"), True)
    
    def test_textile_comment(self):
        
        user = User.objects.create_user('user', 'floguy@gmail.com', password='password')
        topic = TestModel.objects.create(name="Test2")
        
        textile_txt = '''
h2{color:green}. This is a title

h3. This is a subhead

p{color:red}. This is some text of dubious character. Isn't the use of "quotes" just lazy ... writing -- and theft of 'intellectual property' besides? I think the time has come to see a block quote.

bq[fr]. This is a block quote. I'll admit it's not the most exciting block quote ever devised.

Simple list:

#{color:blue} one
# two
# three

Multi-level list:

# one
## aye
## bee
## see
# two
## x
## y
# three

Mixed list:

* Point one
* Point two
## Step 1
## Step 2
## Step 3
* Point three
** Sub point 1
** Sub point 2


Well, that went well. How about we insert an <a href="/" title="watch out">old-fashioned ... hypertext link</a>? Will the quote marks in the tags get messed up? No!

"This is a link (optional title)":http://www.textism.com

table{border:1px solid black}.
|_. this|_. is|_. a|_. header|
<{background:gray}. |\2. this is|{background:red;width:200px}. a|^<>{height:200px}. row|
|this|<>{padding:10px}. is|^. another|(bob#bob). row|

An image:

!/common/textist.gif(optional alt text)!

# Librarians rule
# Yes they do
# But you knew that

Some more text of dubious character. Here is a noisome string of CAPITAL letters. Here is ... something we want to _emphasize_. 
That was a linebreak. And something to indicate *strength*. Of course I could use <em>my ... own HTML tags</em> if I <strong>felt</strong> like it.

h3. Coding

This <code>is some code, "isn't it"</code>. Watch those quote marks! Now for some preformatted text:

<pre>
<code>
	$text = str_replace("<p>%::%</p>","",$text);
	$text = str_replace("%::%</p>","",$text);
	$text = str_replace("%::%","",$text);

</code>
</pre>

This isn't code.


So you see, my friends:

* The time is now
* The time is not later
* The time is not yesterday
* We must act
'''

        comment_textile = ThreadedComment.objects.create_for_object(
            topic, user = user, ip_address = '127.0.0.1', markup = TEXTILE,
            comment = textile_txt,
        )
        c = Context({
            'comment': comment_textile
        })
        s = Template("{% load threadedcommentstags %}{% auto_transform_markup comment %}").render(c)
        self.assertEquals("<h3>" in s, True)
    
    def test_rest_comment(self):
        
        user = User.objects.create_user('user', 'floguy@gmail.com', password='password')
        topic = TestModel.objects.create(name="Test2")
        
        rest_txt = '''
FooBar Header
=============
reStructuredText is **nice**. It has its own webpage_.

A table:

=====  =====  ======
   Inputs     Output
------------  ------
  A      B    A or B
=====  =====  ======
False  False  False
True   False  True
False  True   True
True   True   True
=====  =====  ======

RST TracLinks
-------------

See also ticket `#42`::.

.. _webpage: http://docutils.sourceforge.net/rst.html
'''

        comment_rest = ThreadedComment.objects.create_for_object(
            topic, user = user, ip_address = '127.0.0.1', markup = REST,
            comment = rest_txt,
        )
        c = Context({
            'comment': comment_rest
        })
        s = Template("{% load threadedcommentstags %}{% auto_transform_markup comment %}").render(c)
        self.assertEquals(s.startswith('<p>reStructuredText is'), True)
    
    def test_plaintext_comment(self):
        
        user = User.objects.create_user('user', 'floguy@gmail.com', password='password')
        topic = TestModel.objects.create(name="Test2")
        
        comment_plaintext = ThreadedComment.objects.create_for_object(
            topic, user = user, ip_address = '127.0.0.1', markup = PLAINTEXT,
            comment = '<b>This is Funny</b>',
        )
        c = Context({
            'comment': comment_plaintext
        })
        self.assertEquals(
            Template("{% load threadedcommentstags %}{% auto_transform_markup comment %}").render(c),
            u'&lt;b&gt;This is Funny&lt;/b&gt;'
        )

        comment_plaintext = ThreadedComment.objects.create_for_object(
            topic, user = user, ip_address = '127.0.0.1', markup = PLAINTEXT,
            comment = '<b>This is Funny</b>',
        )
        c = Context({
            'comment': comment_plaintext
        })
        self.assertEquals(
            Template("{% load threadedcommentstags %}{% auto_transform_markup comment as abc %}{{ abc }}").render(c),
            u'&lt;b&gt;This is Funny&lt;/b&gt;'
        )
    
    def test_gravatar_tags(self):
        c = Context({
            'email': "floguy@gmail.com",
            'rating': "G",
            'size': 30,
            'default': 'overridectx',
        })
        self.assertEquals(
            Template('{% load gravatar %}{% get_gravatar_url for email %}').render(c),
            u'http://www.gravatar.com/avatar.php?gravatar_id=04d6b8e8d3c68899ac88eb8623392150&rating=R&size=80&default=img%3Ablank'
        )
        self.assertEquals(
            Template('{% load gravatar %}{% get_gravatar_url for email as var %}Var: {{ var }}').render(c),
            u'Var: http://www.gravatar.com/avatar.php?gravatar_id=04d6b8e8d3c68899ac88eb8623392150&rating=R&size=80&default=img%3Ablank'
        )
        self.assertEquals(
            Template('{% load gravatar %}{% get_gravatar_url for email size 30 rating "G" default override as var %}Var: {{ var }}').render(c),
            u'Var: http://www.gravatar.com/avatar.php?gravatar_id=04d6b8e8d3c68899ac88eb8623392150&rating=G&size=30&default=override'
        )
        self.assertEquals(
            Template('{% load gravatar %}{% get_gravatar_url for email size size rating rating default default as var %}Var: {{ var }}').render(c),
            u'Var: http://www.gravatar.com/avatar.php?gravatar_id=04d6b8e8d3c68899ac88eb8623392150&rating=G&size=30&default=overridectx'
        )
        self.assertEquals(
            Template('{% load gravatar %}{{ email|gravatar }}').render(c),
            u'http://www.gravatar.com/avatar.php?gravatar_id=04d6b8e8d3c68899ac88eb8623392150&rating=R&size=80&default=img%3Ablank'
        )