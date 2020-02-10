from django.test import TestCase

from ..validators import valid_javascript_identifier, valid_jsonp_callback_value


class ValidatorTest(TestCase):
    def test_valid_javascript_identifier(self):
        """
        The function ``valid_javascript_identifier`` validates a given identifier
        according to the latest draft of the ECMAScript 5 Specification
        """
        self.assertTrue(valid_javascript_identifier(b"hello"))

        self.assertFalse(valid_javascript_identifier(b"alert()"))

        self.assertFalse(valid_javascript_identifier(b"a-b"))

        self.assertFalse(valid_javascript_identifier(b"23foo"))

        self.assertTrue(valid_javascript_identifier(b"foo23"))

        self.assertTrue(valid_javascript_identifier(b"$210"))

        self.assertTrue(valid_javascript_identifier("Stra\u00dfe"))

        self.assertTrue(valid_javascript_identifier(br"\u0062"))  # 'b'

        self.assertFalse(valid_javascript_identifier(br"\u62"))

        self.assertFalse(valid_javascript_identifier(br"\u0020"))

        self.assertTrue(valid_javascript_identifier(b"_bar"))

        self.assertTrue(valid_javascript_identifier(b"some_var"))

        self.assertTrue(valid_javascript_identifier(b"$"))

    def test_valid_jsonp_callback_value(self):
        """
        But ``valid_jsonp_callback_value`` is the function you want to use for
        validating JSON-P callback parameter values:
        """

        self.assertTrue(valid_jsonp_callback_value("somevar"))

        self.assertFalse(valid_jsonp_callback_value("function"))

        self.assertFalse(valid_jsonp_callback_value(" somevar"))

        # It supports the possibility of '.' being present in the callback name, e.g.

        self.assertTrue(valid_jsonp_callback_value("$.ajaxHandler"))

        self.assertFalse(valid_jsonp_callback_value("$.23"))

        # As well as the pattern of providing an array index lookup, e.g.

        self.assertTrue(valid_jsonp_callback_value("array_of_functions[42]"))

        self.assertTrue(valid_jsonp_callback_value("array_of_functions[42][1]"))

        self.assertTrue(valid_jsonp_callback_value("$.ajaxHandler[42][1].foo"))

        self.assertFalse(valid_jsonp_callback_value("array_of_functions[42]foo[1]"))

        self.assertFalse(valid_jsonp_callback_value("array_of_functions[]"))

        self.assertFalse(valid_jsonp_callback_value('array_of_functions["key"]'))
