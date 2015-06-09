from django.conf import settings
from django.core.management.base import NoArgsCommand, CommandError

import os
import re
from shutil import rmtree

from dbgettext.registry import registry
from dbgettext.parser import parsed_gettext

INVALID_ESCAPE_SEQUENCES = re.compile(r'[\a\b\f\r\v]')
# (see xgettext's write-po.c)

def recursive_getattr(obj, attr, default=None, separator='__'):
    """ Allows getattr(obj, 'related_class__property__subproperty__etc') """
    try:
        if attr.find(separator) > 0:
            bits = attr.split(separator)
            return recursive_getattr(getattr(obj, bits[0]),
                                     separator.join(bits[1:]), default)
        else:
            return getattr(obj, attr)
    except AttributeError:
        return default


def get_field_or_callable_content(obj, attr_name):
    """ Returns value of obj.attr_name() or obj.attr_name """
    try:
        attr = getattr(obj, attr_name)
    except AttributeError:
        raise

    if callable(attr):
        return attr()
    else:
        return attr


def build_queryset(model, queryset=None, trail=[]):
    """ Recursively creates queryset for model using options """

    try:
        options = registry._registry[model]
    except:
        raise Exception("%s is not registered with dbgettext" % model)

    if queryset is None:
        queryset = model.objects.all()

    recursive_criteria = {}
    for c in options.translate_if:
        recursive_criteria['__'.join(trail+[c])] = options.translate_if[c]
    queryset = queryset.filter(**recursive_criteria)

    if options.parent:
        parent_model = \
            getattr(model,options.parent).field.related.parent_model
        queryset = build_queryset(parent_model, queryset,
                                  trail+[options.parent])

    return queryset


def build_path(obj):
    """ Recursively constructs path for object using options """

    model = type(obj)
    options = registry._registry[model]
    if options.parent:
        path = build_path(getattr(obj, options.parent))
    else:
        path = os.path.join(model._meta.app_label,model._meta.module_name)
    return os.path.join(path, options.get_path_identifier(obj))

def sanitise_message(message):
    """ Prepare message for storage in .po file. """
    return INVALID_ESCAPE_SEQUENCES.sub('', message)

class Command(NoArgsCommand):
    """ dbgettext_export management command """

    # overridable path settings (default: project_root/locale/dbgettext/...)
    path = getattr(settings, 'DBGETTEXT_PATH', 'locale/')
    root = getattr(settings, 'DBGETTEXT_ROOT', 'dbgettext')

    def handle_noargs(self, **options):
        if not os.path.exists(self.path):
            raise CommandError('This command must be run from the project '
                               'root directory, and the %s '
                               '(settings.DBGETTEXT_PATH) directory must '
                               'exist.' % self.path)
        self.gettext()

    help = ('Extract translatable strings from models in database '
            'and store in static files for makemessages to pick up.')

    def gettext(self):
        """ Export translatable strings from models into static files """

        def write(file, string):
            string = string.replace('"','\\"') # prevent """"
            string = '# -*- coding: utf-8 -*-\ngettext("""%s""")\n' % string
            file.write(string.encode('utf8'))

        root = os.path.join(self.path, self.root)

        # remove any old files
        if os.path.exists(root):
            rmtree(root)

        # for each registered model:
        for model, options in registry._registry.items():
            for obj in build_queryset(model):
                path = os.path.join(root, build_path(obj))

                if not os.path.exists(path):
                    os.makedirs(path)

                for attr_name in options.attributes:
                    attr = get_field_or_callable_content(obj, attr_name)
                    if attr:
                        f = open(os.path.join(path, '%s.py' % attr_name), 'wb')
                        write(f, sanitise_message(attr))
                        f.close()

                for attr_name in options.parsed_attributes:
                    f = open(os.path.join(path, '%s.py' % attr_name), 'wb')
                    for s in parsed_gettext(obj, attr_name, export=True):
                        write(f, sanitise_message(s))
                    f.close()
