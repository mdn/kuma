#-*- coding:utf-8 -*-
#
# Copyright (C) 2008 - Olivier Lauzanne <olauzanne@gmail.com>
#
# Distributed under the BSD license, see LICENSE.txt
from cssselectpatch import selector_to_xpath
from lxml import etree
import lxml.html
from copy import deepcopy
from urlparse import urljoin

def fromstring(context, parser=None):
    """use html parser if we don't have clean xml
    """
    if parser == None:
        try:
            return [etree.fromstring(context)]
        except etree.XMLSyntaxError:
            return [lxml.html.fromstring(context)]
    elif parser == 'xml':
        return [etree.fromstring(context)]
    elif parser == 'html':
        return [lxml.html.fromstring(context)]
    elif parser == 'html_fragments':
        return lxml.html.fragments_fromstring(context)
    else:
        ValueError('No such parser: "%s"' % parser)

class NoDefault(object):
    def __repr__(self):
        """clean representation in Sphinx"""
        return '<NoDefault>'

no_default = NoDefault()
del NoDefault

class FlexibleElement(object):
    """property to allow a flexible api"""
    def __init__(self, pget, pset=no_default, pdel=no_default):
        self.pget = pget
        self.pset = pset
        self.pdel = pdel
    def __get__(self, instance, klass):
        class _element(object):
            """real element to support set/get/del attr and item and js call
            style"""
            def __call__(prop, *args, **kwargs):
                return self.pget(instance, *args, **kwargs)
            __getattr__ = __getitem__ = __setattr__ = __setitem__ = __call__
            def __delitem__(prop, name):
                if self.pdel is not no_default:
                    return self.pdel(instance, name)
                else:
                    raise NotImplementedError()
            __delattr__ = __delitem__
            def __repr__(prop):
                return '<flexible_element %s>' % self.pget.func_name
        return _element()
    def __set__(self, instance, value):
        if self.pset is not no_default:
            self.pset(instance, value)
        else:
            raise NotImplementedError()

class PyQuery(list):
    """The main class
    """
    def __init__(self, *args, **kwargs):
        html = None
        elements = []
        self._base_url = None
        self.parser = kwargs.get('parser', None)
        if 'parser' in kwargs:
            del kwargs['parser']
        if not kwargs and len(args) == 1 and isinstance(args[0], basestring) \
           and args[0].startswith('http://'):
            kwargs = {'url': args[0]}
            args = []

        if 'parent' in kwargs:
            self._parent = kwargs.pop('parent')
        else:
            self._parent = no_default

        if kwargs:
            # specific case to get the dom
            if 'filename' in kwargs:
                html = file(kwargs['filename']).read()
            elif 'url' in kwargs:
                url = kwargs.pop('url')
                if 'opener' in kwargs:
                    opener = kwargs.pop('opener')
                    html = opener(url)
                else:
                    from urllib2 import urlopen
                    html = urlopen(url).read()
                self._base_url = url
            else:
                raise ValueError('Invalid keyword arguments %s' % kwargs)
            elements = fromstring(html, self.parser)
        else:
            # get nodes

            # determine context and selector if any
            selector = context = no_default
            length = len(args)
            if len(args) == 1:
                context = args[0]
            elif len(args) == 2:
                selector, context = args
            else:
                raise ValueError("You can't do that." +\
                        " Please, provide arguments")

            # get context
            if isinstance(context, basestring):
                try:
                    elements = fromstring(context, self.parser)
                except Exception, e:
                    raise ValueError('%r, %s' % (e, context))
            elif isinstance(context, self.__class__):
                # copy
                elements = context[:]
            elif isinstance(context, list):
                elements = context
            elif isinstance(context, etree._Element):
                elements = [context]

            # select nodes
            if elements and selector is not no_default:
                xpath = selector_to_xpath(selector)
                results = [tag.xpath(xpath) for tag in elements]
                # Flatten the results
                elements = []
                for r in results:
                    elements.extend(r)

        list.__init__(self, elements)

    def __call__(self, *args):
        """return a new PyQuery instance
        """
        length = len(args)
        if length == 0:
            raise ValueError('You must provide at least a selector')
        if len(args) == 1 and not args[0].startswith('<'):
            args += (self,)
        result = self.__class__(*args, **dict(parent=self))
        return result

    # keep original list api prefixed with _
    _append = list.append
    _extend = list.extend

    # improve pythonic api
    def __add__(self, other):
        assert isinstance(other, self.__class__)
        return self.__class__(self[:] + other[:])

    def extend(self, other):
        assert isinstance(other, self.__class__)
        self._extend(other[:])

    def __str__(self):
        """xml representation of current nodes::

            >>> xml = PyQuery('<script><![[CDATA[ ]></script>', parser='html_fragments')
            >>> print str(xml)
            <script>&lt;![[CDATA[ ]&gt;</script>

        """
        return ''.join([etree.tostring(e) for e in self])

    def __html__(self):
        """html representation of current nodes::

            >>> html = PyQuery('<script><![[CDATA[ ]></script>', parser='html_fragments')
            >>> print html.__html__()
            <script><![[CDATA[ ]></script>

        """
        return ''.join([lxml.html.tostring(e) for e in self])

    def __repr__(self):
        r = []
        try:
            for el in self:
                c = el.get('class')
                c = c and '.' + '.'.join(c.split(' ')) or ''
                id = el.get('id')
                id = id and '#' + id or ''
                r.append('<%s%s%s>' % (el.tag, id, c))
            return '[' + (', '.join(r)) + ']'
        except AttributeError:
            return list.__repr__(self)


    ##############
    # Traversing #
    ##############

    def _filter_only(self, selector, elements, reverse=False, unique=False):
        """Filters the selection set only, as opposed to also including
           descendants.
        """
        if selector is None:
            results = elements
        else:
            xpath = selector_to_xpath(selector, 'self::')
            results = []
            for tag in elements:
                results.extend(tag.xpath(xpath))
        if reverse:
            results.reverse()
        if unique:
            result_list = results
            results = []
            for item in result_list:
                if not item in results:
                    results.append(item)
        return self.__class__(results, **dict(parent=self))

    def parent(self, selector=None):
        return self._filter_only(selector, [e.getparent() for e in self if e.getparent() is not None], unique = True)

    def prev(self, selector=None):
        return self._filter_only(selector, [e.getprevious() for e in self if e.getprevious() is not None])

    def next(self, selector=None):
        return self._filter_only(selector, [e.getnext() for e in self if e.getnext() is not None])

    def _traverse(self, method):
        for e in self:
            current = getattr(e, method)()
            while current is not None:
                yield current
                current = getattr(current, method)()

    def _traverse_parent_topdown(self):
        for e in self:
            this_list = []
            current = e.getparent()
            while current is not None:
                this_list.append(current)
                current = current.getparent()
            this_list.reverse()
            for j in this_list:
                yield j

    def _nextAll(self):
        return [e for e in self._traverse('getnext')]

    def nextAll(self, selector=None):
        """
            >>> d = PyQuery('<span><p class="hello">Hi</p><p>Bye</p><img scr=""/></span>')
            >>> d('p:last').nextAll()
            [<img>]
        """
        return self._filter_only(selector, self._nextAll())

    def _prevAll(self):
        return [e for e in self._traverse('getprevious')]

    def prevAll(self, selector=None):
        """
            >>> d = PyQuery('<span><p class="hello">Hi</p><p>Bye</p><img scr=""/></span>')
            >>> d('p:last').prevAll()
            [<p.hello>]
        """
        return self._filter_only(selector, self._prevAll(), reverse = True)

    def siblings(self, selector=None):
        """
            >>> d = PyQuery('<span><p class="hello">Hi</p><p>Bye</p><img scr=""/></span>')
            >>> d('.hello').siblings()
            [<p>, <img>]
            >>> d('.hello').siblings('img')
            [<img>]
        """
        return self._filter_only(selector, self._prevAll() + self._nextAll())

    def parents(self, selector=None):
        """
            >>> d = PyQuery('<span><p class="hello">Hi</p><p>Bye</p></span>')
            >>> d('p').parents()
            [<span>]
            >>> d('.hello').parents('span')
            [<span>]
            >>> d('.hello').parents('p')
            []
        """
        return self._filter_only(
                selector,
                [e for e in self._traverse_parent_topdown()],
                unique = True
            )

    def children(self, selector=None):
        """Filter elements that are direct children of self using optional selector.

            >>> d = PyQuery('<span><p class="hello">Hi</p><p>Bye</p></span>')
            >>> d
            [<span>]
            >>> d.children()
            [<p.hello>, <p>]
            >>> d.children('.hello')
            [<p.hello>]
        """
        elements = [child for tag in self for child in tag.getchildren()]
        return self._filter_only(selector, elements)

    def closest(self, selector=None):
        """
            >>> d = PyQuery('<div class="hello"><p>This is a <strong class="hello">test</strong></p></div>')
            >>> d('strong').closest('div')
            [<div.hello>]
            >>> d('strong').closest('.hello')
            [<strong.hello>]
            >>> d('strong').closest('form')
            []
        """
        try:
            current = self[0]
        except IndexError:
            current = None
        while current is not None and not self.__class__(current).is_(selector):
            current = current.getparent()
        return self.__class__(current, **dict(parent=self))

    def filter(self, selector):
        """Filter elements in self using selector (string or function).

            >>> d = PyQuery('<p class="hello">Hi</p><p>Bye</p>')
            >>> d('p')
            [<p.hello>, <p>]
            >>> d('p').filter('.hello')
            [<p.hello>]
            >>> d('p').filter(lambda i: i == 1)
            [<p>]
            >>> d('p').filter(lambda i: PyQuery(this).text() == 'Hi')
            [<p.hello>]
        """
        if not callable(selector):
            return self._filter_only(selector, self)
        else:
            elements = []
            try:
                for i, this in enumerate(self):
                    selector.func_globals['this'] = this
                    if selector(i):
                        elements.append(this)
            finally:
                del selector.func_globals['this']
            return self.__class__(elements, **dict(parent=self))

    def not_(self, selector):
        """Return elements that don't match the given selector.

            >>> d = PyQuery('<p class="hello">Hi</p><p>Bye</p><div></div>')
            >>> d('p').not_('.hello')
            [<p>]
        """
        exclude = set(self.__class__(selector, self))
        return self.__class__([e for e in self if e not in exclude], **dict(parent=self))

    def is_(self, selector):
        """Returns True if selector matches at least one current element, else False.
            >>> d = PyQuery('<p class="hello">Hi</p><p>Bye</p><div></div>')
            >>> d('p').eq(0).is_('.hello')
            True
            >>> d('p').eq(1).is_('.hello')
            False
        """
        return bool(self.__class__(selector, self))

    def find(self, selector):
        """Find elements using selector traversing down from self.

            >>> m = '<p><span><em>Whoah!</em></span></p><p><em> there</em></p>'
            >>> d = PyQuery(m)
            >>> d('p').find('em')
            [<em>, <em>]
            >>> d('p').eq(1).find('em')
            [<em>]
        """
        xpath = selector_to_xpath(selector)
        results = [child.xpath(xpath) for tag in self for child in tag.getchildren()]
        # Flatten the results
        elements = []
        for r in results:
            elements.extend(r)
        return self.__class__(elements, **dict(parent=self))

    def eq(self, index):
        """Return PyQuery of only the element with the provided index.

            >>> d = PyQuery('<p class="hello">Hi</p><p>Bye</p><div></div>')
            >>> d('p').eq(0)
            [<p.hello>]
            >>> d('p').eq(1)
            [<p>]
            >>> d('p').eq(2)
            []
        """
        # Use slicing to silently handle out of bounds indexes
        items = self[index:index+1]
        return self.__class__(items, **dict(parent=self))

    def each(self, func):
        """apply func on each nodes
        """
        for e in self:
            func(self.__class__([e]))
        return self

    def map(self, func):
        """Returns a new PyQuery after transforming current items with func.

        func should take two arguments - 'index' and 'element'.  Elements can
        also be referred to as 'this' inside of func.

            >>> d = PyQuery('<p class="hello">Hi there</p><p>Bye</p><br />')
            >>> d('p').map(lambda i, e: PyQuery(e).text())
            ['Hi there', 'Bye']

            >>> d('p').map(lambda i, e: len(PyQuery(this).text()))
            [8, 3]

            >>> d('p').map(lambda i, e: PyQuery(this).text().split())
            ['Hi', 'there', 'Bye']
        """
        items = []
        try:
            for i, element in enumerate(self):
                func.func_globals['this'] = element
                result = func(i, element)
                if result is not None:
                    if not isinstance(result, list):
                        items.append(result)
                    else:
                        items.extend(result)
        finally:
            del func.func_globals['this']
        return self.__class__(items, **dict(parent=self))

    @property
    def length(self):
        return len(self)

    def size(self):
        return len(self)

    def end(self):
        """Break out of a level of traversal and return to the parent level.

            >>> m = '<p><span><em>Whoah!</em></span></p><p><em> there</em></p>'
            >>> d = PyQuery(m)
            >>> d('p').eq(1).find('em').end().end()
            [<p>, <p>]
        """
        return self._parent

    ##############
    # Attributes #
    ##############
    def attr(self, *args, **kwargs):
        """Attributes manipulation
        """

        mapping = {'class_': 'class', 'for_': 'for'}

        attr = value = no_default
        length = len(args)
        if length == 1:
            attr = args[0]
            attr = mapping.get(attr, attr)
        elif length == 2:
            attr, value = args
            attr = mapping.get(attr, attr)
        elif kwargs:
            attr = {}
            for k, v in kwargs.items():
                attr[mapping.get(k, k)] = v
        else:
            raise ValueError('Invalid arguments %s %s' % (args, kwargs))

        if not self:
            return None
        elif isinstance(attr, dict):
            for tag in self:
                for key, value in attr.items():
                    tag.set(key, value)
        elif value is no_default:
            return self[0].get(attr)
        elif value is None or value == '':
            return self.removeAttr(attr)
        else:
            for tag in self:
                tag.set(attr, value)
        return self

    def removeAttr(self, name):
        """Remove an attribute::

            >>> d = PyQuery('<div id="myid"></div>')
            >>> d.removeAttr('id')
            [<div>]

        """
        for tag in self:
            del tag.attrib[name]
        return self

    attr = FlexibleElement(pget=attr, pdel=removeAttr)

    #######
    # CSS #
    #######
    def height(self, value=no_default):
        """set/get height of element
        """
        return self.attr('height', value)

    def width(self, value=no_default):
        """set/get width of element
        """
        return self.attr('width', value)

    def hasClass(self, name):
        """Return True if element has class::

            >>> d = PyQuery('<div class="myclass"></div>')
            >>> d.hasClass('myclass')
            True

        """
        return self.is_('.%s' % name)

    def addClass(self, value):
        """Add a css class to elements::

            >>> d = PyQuery('<div></div>')
            >>> d.addClass('myclass')
            [<div.myclass>]

        """
        for tag in self:
            values = value.split(' ')
            classes = set((tag.get('class') or '').split())
            classes = classes.union(values)
            classes.difference_update([''])
            tag.set('class', ' '.join(classes))
        return self

    def removeClass(self, value):
        """Remove a css class to elements

            >>> d = PyQuery('<div class="myclass"></div>')
            >>> d.removeClass('myclass')
            [<div>]

        """
        for tag in self:
            values = value.split(' ')
            classes = set((tag.get('class') or '').split())
            classes.difference_update(values)
            classes.difference_update([''])
            tag.set('class', ' '.join(classes))
        return self

    def toggleClass(self, value):
        """Toggle a css class to elements

            >>> d = PyQuery('<div></div>')
            >>> d.toggleClass('myclass')
            [<div.myclass>]

        """
        for tag in self:
            values = set(value.split(' '))
            classes = set((tag.get('class') or '').split())
            values_to_add = values.difference(classes)
            classes.difference_update(values)
            classes = classes.union(values_to_add)
            classes.difference_update([''])
            tag.set('class', ' '.join(classes))
        return self

    def css(self, *args, **kwargs):
        """css attributes manipulation
        """

        attr = value = no_default
        length = len(args)
        if length == 1:
            attr = args[0]
        elif length == 2:
            attr, value = args
        elif kwargs:
            attr = kwargs
        else:
            raise ValueError('Invalid arguments %s %s' % (args, kwargs))

        if isinstance(attr, dict):
            for tag in self:
                stripped_keys = [key.strip().replace('_', '-')
                                 for key in attr.keys()]
                current = [el.strip()
                           for el in (tag.get('style') or '').split(';')
                           if el.strip()
                           and not el.split(':')[0].strip() in stripped_keys]
                for key, value in attr.items():
                    key = key.replace('_', '-')
                    current.append('%s: %s' % (key, value))
                tag.set('style', '; '.join(current))
        elif isinstance(value, basestring):
            attr = attr.replace('_', '-')
            for tag in self:
                current = [el.strip()
                           for el in (tag.get('style') or '').split(';')
                           if el.strip()
                              and not el.split(':')[0].strip() == attr.strip()]
                current.append('%s: %s' % (attr, value))
                tag.set('style', '; '.join(current))
        return self

    css = FlexibleElement(pget=css, pset=css)

    ###################
    # CORE UI EFFECTS #
    ###################
    def hide(self):
        """add display:none to elements style
        """
        return self.css('display', 'none')

    def show(self):
        """add display:block to elements style
        """
        return self.css('display', 'block')

    ########
    # HTML #
    ########
    def val(self, value=no_default):
        """Set/get the attribute value::

            >>> d = PyQuery('<input />')
            >>> d.val('Youhou')
            [<input>]
            >>> d.val()
            'Youhou'

        """
        return self.attr('value', value)

    def html(self, value=no_default):
        """Get or set the html representation of sub nodes.

        Get the text value::

            >>> doc = PyQuery('<div><span>toto</span></div>')
            >>> print doc.html()
            <span>toto</span>

        Set the text value::

            >>> doc.html('<span>Youhou !</span>')
            [<div>]
            >>> print doc
            <div><span>Youhou !</span></div>
        """
        if value is no_default:
            if not self:
                return None
            tag = self[0]
            children = tag.getchildren()
            if not children:
                return tag.text
            html = tag.text or ''
            html += ''.join(map(lambda x: etree.tostring(x, encoding=unicode), children))
            return html
        else:
            if isinstance(value, self.__class__):
                new_html = str(value)
            elif isinstance(value, basestring):
                new_html = value

            for tag in self:
                for child in tag.getchildren():
                    tag.remove(child)
                root = fromstring('<root>' + new_html + '</root>', self.parser)[0]
                children = root.getchildren()
                if children:
                    tag.extend(children)
                tag.text = root.text
                tag.tail = root.tail
        return self

    def text(self, value=no_default):
        """Get or set the text representation of sub nodes.

        Get the text value::

            >>> doc = PyQuery('<div><span>toto</span><span>tata</span></div>')
            >>> print doc.text()
            toto tata

        Set the text value::

            >>> doc.text('Youhou !')
            [<div>]
            >>> print doc
            <div>Youhou !</div>

        """

        if value is no_default:
            if not self:
                return None

            text = []

            def add_text(tag, no_tail=False):
                if tag.text:
                    text.append(tag.text)
                for child in tag.getchildren():
                    add_text(child)
                if not no_tail and tag.tail:
                    text.append(tag.tail)

            for tag in self:
                add_text(tag, no_tail=True)
            return ' '.join([t.strip() for t in text if t.strip()])

        for tag in self:
            for child in tag.getchildren():
                tag.remove(child)
            tag.text = value
        return self

    ################
    # Manipulating #
    ################

    def _get_root(self, value):
        if  isinstance(value, basestring):
            root = fromstring('<root>' + value + '</root>', self.parser)[0]
        elif isinstance(value, etree._Element):
            root = self.__class__(value)
        elif isinstance(value, PyQuery):
            root = value
        else:
            raise TypeError(
            'Value must be string, PyQuery or Element. Got %r' %  value)
        if hasattr(root, 'text') and isinstance(root.text, basestring):
            root_text = root.text
        else:
            root_text = ''
        return root, root_text

    def append(self, value):
        """append value to each nodes
        """
        root, root_text = self._get_root(value)
        for i, tag in enumerate(self):
            if len(tag) > 0: # if the tag has children
                last_child = tag[-1]
                if not last_child.tail:
                    last_child.tail = ''
                last_child.tail += root_text
            else:
                if not tag.text:
                    tag.text = ''
                tag.text += root_text
            if i > 0:
                root = deepcopy(list(root))
            tag.extend(root)
            root = tag[-len(root):]
        return self

    def appendTo(self, value):
        """append nodes to value
        """
        value.append(self)
        return self

    def prepend(self, value):
        """prepend value to nodes
        """
        root, root_text = self._get_root(value)
        for i, tag in enumerate(self):
            if not tag.text:
                tag.text = ''
            if len(root) > 0:
                root[-1].tail = tag.text
                tag.text = root_text
            else:
                tag.text = root_text + tag.text
            if i > 0:
                root = deepcopy(list(root))
            tag[:0] = root
            root = tag[:len(root)]
        return self

    def prependTo(self, value):
        """prepend nodes to value
        """
        value.prepend(self)
        return self

    def after(self, value):
        """add value after nodes
        """
        root, root_text = self._get_root(value)
        for i, tag in enumerate(self):
            if not tag.tail:
                tag.tail = ''
            tag.tail += root_text
            if i > 0:
                root = deepcopy(list(root))
            parent = tag.getparent()
            index = parent.index(tag) + 1
            parent[index:index] = root
            root = parent[index:len(root)]
        return self

    def insertAfter(self, value):
        """insert nodes after value
        """
        value.after(self)
        return self

    def before(self, value):
        """insert value before nodes
        """
        root, root_text = self._get_root(value)
        for i, tag in enumerate(self):
            previous = tag.getprevious()
            if previous != None:
                if not previous.tail:
                    previous.tail = ''
                previous.tail += root_text
            else:
                parent = tag.getparent()
                if not parent.text:
                    parent.text = ''
                parent.text += root_text
            if i > 0:
                root = deepcopy(list(root))
            parent = tag.getparent()
            index = parent.index(tag)
            parent[index:index] = root
            root = parent[index:len(root)]
        return self

    def insertBefore(self, value):
        """insert nodes before value
        """
        value.before(self)
        return self

    def wrap(self, value):
        """A string of HTML that will be created on the fly and wrapped around
        each target::

            >>> d = PyQuery('<span>youhou</span>')
            >>> d.wrap('<div></div>')
            [<div>]
            >>> print d
            <div><span>youhou</span></div>

        """
        assert isinstance(value, basestring)
        value = fromstring(value)[0]
        nodes = []
        for tag in self:
            wrapper = deepcopy(value)
            # FIXME: using iterchildren is probably not optimal
            if not wrapper.getchildren():
                wrapper.append(deepcopy(tag))
            else:
                childs = [c for c in wrapper.iterchildren()]
                child = childs[-1]
                child.append(deepcopy(tag))
            nodes.append(wrapper)

            parent = tag.getparent()
            if parent is not None:
                for t in parent.iterchildren():
                    if t is tag:
                        t.addnext(wrapper)
                        parent.remove(t)
                        break
        self[:] = nodes
        return self

    def wrapAll(self, value):
        """Wrap all the elements in the matched set into a single wrapper element::

            >>> d = PyQuery('<div><span>Hey</span><span>you !</span></div>')
            >>> print d('span').wrapAll('<div id="wrapper"></div>')
            <div id="wrapper"><span>Hey</span><span>you !</span></div>

        """
        if not self:
            return self

        assert isinstance(value, basestring)
        value = fromstring(value)[0]
        wrapper = deepcopy(value)
        if not wrapper.getchildren():
            child = wrapper
        else:
            childs = [c for c in wrapper.iterchildren()]
            child = childs[-1]

        replace_childs = True
        parent = self[0].getparent()
        if parent is None:
            parent = no_default

        # add nodes to wrapper and check parent
        for tag in self:
            child.append(deepcopy(tag))
            if tag.getparent() is not parent:
                replace_childs = False

        # replace nodes i parent if possible
        if parent is not no_default and replace_childs:
            childs = [c for c in parent.iterchildren()]
            if len(childs) == len(self):
                for tag in self:
                    parent.remove(tag)
                parent.append(wrapper)

        self[:] = [wrapper]
        return self

    def replaceWith(self, value):
        """replace nodes by value
        """
        if callable(value):
            for i, element in enumerate(self):
                self.__class__(element).before(value(i, element) + (element.tail or ''))
                parent = element.getparent()
                parent.remove(element)
        else:
            for tag in self:
                self.__class__(tag).before(value + (tag.tail or ''))
                parent = tag.getparent()
                parent.remove(tag)
        return self

    def replaceAll(self, expr):
        """replace nodes by expr
        """
        if self._parent is no_default:
            raise ValueError(
                    'replaceAll can only be used with an object with parent')
        self._parent(expr).replaceWith(self)
        return self

    def clone(self):
        """return a copy of nodes
        """
        self[:] = [deepcopy(tag) for tag in self]
        return self

    def empty(self):
        """remove nodes content
        """
        for tag in self:
            tag.text = None
            tag[:] = []
        return self

    def remove(self, expr=no_default):
        """remove nodes
        """
        if expr is no_default:
            for tag in self:
                parent = tag.getparent()
                if parent is not None:
                    if tag.tail:
                        if not parent.text:
                            parent.text = ''
                        parent.text += ' ' + tag.tail
                    parent.remove(tag)
        else:
            results = self.__class__(expr, self)
            results.remove()
        return self

    #####################################################
    # Additional methods that are not in the jQuery API #
    #####################################################

    @property
    def base_url(self):
        """Return the url of current html document or None if not available.
        """
        if self._base_url is not None:
            return self._base_url
        if self._parent is not no_default:
            return self._parent.base_url

    def make_links_absolute(self, base_url=None):
        """Make all links absolute.
        """
        if base_url is None:
            base_url = self.base_url
            if base_url is None:
                raise ValueError('You need a base URL to make your links'
                 'absolute. It can be provided by the base_url parameter.')

        self('a').each(lambda a:
                       a.attr('href', urljoin(base_url, a.attr('href'))))
        return self
