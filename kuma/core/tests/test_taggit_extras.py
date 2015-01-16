from django.test import TestCase

from .taggit_extras.models import Food


class NamespacedTaggableManagerTest(TestCase):
    food_model = Food

    def assert_tags_equal(self, qs, tags, sort=True, attr="name"):
        got = map(lambda tag: getattr(tag, attr), qs)
        if sort:
            got.sort()
            tags.sort()
        self.assertEqual(got, tags)

    def test_all_ns(self):
        """Tags can be collated or fetched by namespace"""
        apple = self.food_model.objects.create(name="apple")

        expected_tags = {
            u'': [u'foo', u'bar', u'baz'],
            u'int:': [u'int:1', u'int:2'],
            u'string:': [u'string:asdf'],
            u'color:': [u'color:red'],
            u'system:contest:': [u'system:contest:finalist']
        }

        for tags in expected_tags.values():
            apple.tags.add(*tags)

        ns_tags = apple.tags.all_ns()

        expected_ns = expected_tags.keys()
        expected_ns.sort()
        result_ns = ns_tags.keys()
        result_ns.sort()
        self.assertEqual(expected_ns, result_ns)

        for ns in expected_ns:
            self.assert_tags_equal(ns_tags[ns], expected_tags[ns])
            self.assert_tags_equal(apple.tags.all_ns(ns), expected_tags[ns])

    def test_clear_ns(self):
        """Tags can be selectively cleared by namespace"""
        apple = self.food_model.objects.create(name="apple")
        tags_cleared = ['a:1', 'a:2', 'a:3']
        tags_not_cleared = ['1', '2', 'b:1', 'b:2', 'c:1']
        apple.tags.add(*tags_cleared)
        apple.tags.add(*tags_not_cleared)
        apple.tags.clear_ns('a:')
        self.assert_tags_equal(apple.tags.all(), tags_not_cleared)

    def test_set_ns(self):
        """Tags can be selectively set by namespace"""
        apple = self.food_model.objects.create(name="apple")

        tags_before_set = ['a:1', 'a:2', 'a:3']
        tags_after_set = ['a:4', 'a:5', 'a:6']
        tags_not_set = ['1', '2', 'b:1', 'b:2', 'c:1']

        apple.tags.add(*tags_before_set)
        apple.tags.add(*tags_not_set)

        apple.tags.set_ns('a:', *tags_after_set)

        self.assert_tags_equal(apple.tags.all(), tags_after_set + tags_not_set)

    def test_add_ns(self):
        """Tags that do not start with the namespace will be added with the
        namespace tacked on."""
        apple = self.food_model.objects.create(name="apple")

        tags = ['foo', 'bar', 'baz']
        apple.tags.add_ns('a:', *tags)

        self.assert_tags_equal(apple.tags.all(), ['a:%s' % t for t in tags])
