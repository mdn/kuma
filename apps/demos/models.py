from datetime import datetime
from time import strftime
from os import unlink, makedirs
from os.path import basename, dirname, isfile, isdir
from shutil import rmtree
import re

import logging

import zipfile
import tarfile
import magic

from django.conf import settings

from django.utils.encoding import smart_unicode, smart_str

from devmo.urlresolvers import reverse

from django.core.exceptions import ValidationError

from django.db import models
from django.db.models import Q

from django.db.models.fields.files import FieldFile, ImageFieldFile
from django.core.files.storage import FileSystemStorage

from django.utils.translation import ugettext_lazy as _
from django.template.defaultfilters import slugify
from django.template.loader import render_to_string
from django.template.defaultfilters import slugify, filesizeformat

import caching.base

from django.contrib.sites.models import Site
from django.contrib.auth.models import User

import tagging
import tagging.fields
import tagging.models

from tagging.utils import parse_tag_input
from tagging.fields import TagField
from tagging.models import Tag

from threadedcomments.models import ThreadedComment, FreeThreadedComment

from actioncounters.fields import ActionCounterField

from embedutils import VideoEmbedURLField

from . import scale_image
from . import TAG_DESCRIPTIONS, DEMO_LICENSES

try:
    from PIL import Image
except ImportError:
    import Image


THUMBNAIL_MAXW = getattr(settings, 'DEMO_THUMBNAIL_MAX_WIDTH', 200)
THUMBNAIL_MAXH = getattr(settings, 'DEMO_THUMBNAIL_MAX_HEIGHT', 150)

DEMO_MAX_ZIP_FILESIZE = getattr(settings, 'DEMO_MAX_ZIP_FILESIZE', 60 * 1024 * 1024) # 60MB
DEMO_MAX_FILESIZE_IN_ZIP = getattr(settings, 'DEMO_MAX_FILESIZE_IN_ZIP', 60 * 1024 * 1024) # 60MB

# Set up a file system for demo uploads that can be kept separate from the rest
# of /media if necessary. Lots of hackery here to ensure a set of sensible
# defaults are tried.
DEMO_UPLOADS_ROOT = getattr(settings, 'DEMO_UPLOADS_ROOT',
    '%s/uploads/demos' % getattr(settings, 'MEDIA_ROOT', 'media'))
DEMO_UPLOADS_URL = getattr(settings, 'DEMO_UPLOADS_URL',
    '%s/uploads/demos' % getattr(settings, 'MEDIA_URL', '/media'))
demo_uploads_fs = FileSystemStorage(location=DEMO_UPLOADS_ROOT, base_url=DEMO_UPLOADS_URL)

DEMO_MIMETYPE_BLACKLIST = getattr(settings, 'DEMO_FILETYPE_BLACKLIST', [
    'application/msword',
    'application/pdf',
    'application/postscript',
    'application/vnd.lotus-wordpro',
    'application/vnd.ms-cab-compressed',
    'application/vnd.ms-excel',
    'application/vnd.ms-tnef',
    'application/vnd.oasis.opendocument.text',
    'application/vnd.symbian.install',
    'application/x-123',
    'application/x-arc',
    'application/x-archive',
    'application/x-arj',
    'application/x-bittorrent',
    'application/x-bzip2',
    'application/x-compress',
    'application/x-debian-package',
    'application/x-dosexec',
    'application/x-executable',
    'application/x-gzip',
    'application/x-iso9660-image',
    'application/x-java-applet',
    'application/x-java-jce-keystore',
    'application/x-java-keystore',
    'application/x-java-pack200',
    'application/x-lha',
    'application/x-lharc',
    'application/x-lzip',
    'application/x-msaccess',
    'application/x-rar',
    'application/x-rpm',
    'application/x-sc',
    'application/x-setupscript.',
    'application/x-sharedlib',
    'application/x-shockwave-flash',
    'application/x-stuffit',
    'application/x-tar',
    'application/x-zip',
    'application/x-xz',
    'application/x-zoo',
    'application/xml-sitemap',
    'application/zip',
    'model/vrml',
    'model/x3d',
    'text/x-msdos-batch',
    'text/x-perl',
    'text/x-php',
])


def get_root_for_submission(instance):
    """Build a root path for demo submission files"""
    c_name = instance.creator.username
    return '%(h1)s/%(h2)s/%(username)s/%(slug)s' % dict(
         h1=c_name[0], h2=c_name[1], username=c_name, slug=instance.slug,)

def mk_upload_to(field_fn):
    """upload_to builder for file upload fields"""
    def upload_to(instance, filename):
        return '%(base)s/%(field_fn)s' % dict( 
            base=get_root_for_submission(instance), field_fn=field_fn)
    return upload_to


class ConstrainedTagField(tagging.fields.TagField):
    """Tag field constrained to described tags"""

    def __init__(self, *args, **kwargs):
        if 'max_tags' not in kwargs:
            self.max_tags = 5
        else:
            self.max_tags = kwargs['max_tags']
            del kwargs['max_tags']
        super(ConstrainedTagField, self).__init__(*args, **kwargs)

    def validate(self, value, instance):

        if not isinstance(value, (list, tuple)):
            value = parse_tag_input(value)

        if len(value) > self.max_tags:
            raise ValidationError(_('Maximum of %s tags allowed') % 
                    (self.max_tags))

        for tag_name in value:
            if not tag_name in TAG_DESCRIPTIONS:
                raise ValidationError(
                    _('Tag "%s" is not in the set of described tags') % 
                        (tag_name))

    def formfield(self, **kwargs):
        from .forms import ConstrainedTagFormField
        defaults = {'form_class': ConstrainedTagFormField}
        defaults.update(kwargs)
        return super(ConstrainedTagField, self).formfield(**defaults)


class OverwritingFieldFile(FieldFile):
    """The built-in FieldFile alters the filename when saving, if a file with
    that name already exists. This subclass deletes an existing file first so
    that an upload will replace it."""
    # TODO:liberate
    def save(self, name, content, save=True):
        name = self.field.generate_filename(self.instance, name)
        self.storage.delete(name)
        super(OverwritingFieldFile, self).save(name,content,save)
    

class OverwritingFileField(models.FileField):
    # TODO:liberate
    """This field causes an uploaded file to replace an existing one on disk."""
    attr_class = OverwritingFieldFile

    def __init__(self, *args, **kwargs):
        self.max_upload_size = kwargs.pop("max_upload_size")
        super(OverwritingFileField, self).__init__(*args, **kwargs)

    def clean(self, *args, **kwargs):        
        data = super(OverwritingFileField, self).clean(*args, **kwargs)
        
        file = data.file
        try:
            if file._size > self.max_upload_size:
                raise ValidationError(
                    _('Please keep filesize under %s. Current filesize %s') % 
                    (filesizeformat(self.max_upload_size), filesizeformat(file._size))
                )
        except AttributeError:
            pass        
            
        return data


class OverwritingImageFieldFile(ImageFieldFile):
    # TODO:liberate
    """The built-in FieldFile alters the filename when saving, if a file with
    that name already exists. This subclass deletes an existing file first so
    that an upload will replace it."""
    def save(self, name, content, save=True):
        name = self.field.generate_filename(self.instance, name)
        self.storage.delete(name)
        super(OverwritingImageFieldFile, self).save(name,content,save)
    

class OverwritingImageField(models.ImageField):
    # TODO:liberate
    """This field causes an uploaded file to replace an existing one on disk."""
    attr_class = OverwritingImageFieldFile


class SubmissionManager(caching.base.CachingManager):
    """Manager for Submission objects"""

    # TODO: Make these search functions into a mixin?

    # See: http://www.julienphalip.com/blog/2008/08/16/adding-search-django-site-snap/
    def _normalize_query(self, query_string,
                        findterms=re.compile(r'"([^"]+)"|(\S+)').findall,
                        normspace=re.compile(r'\s{2,}').sub):
        ''' Splits the query string in invidual keywords, getting rid of unecessary spaces
            and grouping quoted words together.
            Example:
            
            >>> normalize_query('  some random  words "with   quotes  " and   spaces')
            ['some', 'random', 'words', 'with quotes', 'and', 'spaces']
        
        '''
        return [normspace(' ', (t[0] or t[1]).strip()) for t in findterms(query_string)] 

    # See: http://www.julienphalip.com/blog/2008/08/16/adding-search-django-site-snap/
    def _get_query(self, query_string, search_fields):
        ''' Returns a query, that is a combination of Q objects. That combination
            aims to search keywords within a model by testing the given search fields.
        
        '''
        query = None # Query to search for every search term        
        terms = self._normalize_query(query_string)
        for term in terms:
            or_query = None # Query to search for a given term in each field
            for field_name in search_fields:
                q = Q(**{"%s__icontains" % field_name: term})
                if or_query is None:
                    or_query = q
                else:
                    or_query = or_query | q
            if query is None:
                query = or_query
            else:
                query = query & or_query
        return query

    def search(self, query_string, sort):
        """Quick and dirty keyword search on submissions"""
        # TODO: Someday, replace this with something like Sphinx or another real search engine
        strip_qs = query_string.strip()
        if not strip_qs:
            return self.all_sorted(sort).order_by('-modified')
        else:
            query = self._get_query(strip_qs, ['title', 'summary', 'description',])
            return self.all_sorted(sort).filter(query).order_by('-modified')

    def all_sorted(self, sort=None):
        """Apply to .all() one of the sort orders supported for views"""
        queryset = self.all()
        if sort == 'launches':
            return queryset.order_by('-launches_total')
        elif sort == 'likes':
            return queryset.order_by('-likes_total')
        elif sort == 'upandcoming':
            return queryset.order_by('-launches_recent','-likes_recent')
        else:
            return queryset.order_by('-created')
        

class Submission(caching.base.CachingMixin, models.Model):
    """Representation of a demo submission"""
    objects = SubmissionManager()

    title = models.CharField(
            _("what is your demo's name?"), 
            max_length=255, blank=False, unique=True)
    slug = models.SlugField(_("slug"), 
            blank=False, unique=True)
    summary = models.CharField(
            _("describe your demo in one line"),
            max_length=255, blank=False)
    description = models.TextField(
            _("describe your demo in more detail (optional)"), 
            blank=True)

    featured = models.BooleanField()
    hidden = models.BooleanField()

    navbar_optout = models.BooleanField(
        _('control how your demo is launched'),
        choices=( 
            (True, _('Disable navigation bar, launch demo in a new window')),
            (False, _('Use navigation bar, display demo in <iframe>'))
        )
    )

    comments_total = models.PositiveIntegerField(default=0)

    launches = ActionCounterField()
    likes = ActionCounterField()

    tags = ConstrainedTagField(
            _('select up to 5 tags that describe your demo'),
            max_tags=5)

    screenshot_1 = OverwritingImageField(
            _('Screenshot #1'),
            storage=demo_uploads_fs,
            upload_to=mk_upload_to('screenshot_1.png'), blank=False)
    screenshot_2 = OverwritingImageField(
            _('Screenshot #2'),
            storage=demo_uploads_fs,
            upload_to=mk_upload_to('screenshot_2.png'), blank=True)
    screenshot_3 = OverwritingImageField(
            _('Screenshot #3'),
            storage=demo_uploads_fs,
            upload_to=mk_upload_to('screenshot_3.png'), blank=True)
    screenshot_4 = OverwritingImageField(
            _('Screenshot #4'),
            storage=demo_uploads_fs,
            upload_to=mk_upload_to('screenshot_4.png'), blank=True)
    screenshot_5 = OverwritingImageField(
            _('Screenshot #5'),
            storage=demo_uploads_fs,
            upload_to=mk_upload_to('screenshot_5.png'), blank=True)

    video_url = VideoEmbedURLField(
            _("have a video of your demo in action? (optional)"),
            verify_exists=False, blank=True, null=True)

    demo_package = OverwritingFileField(
            _('select a ZIP file containing your demo'),
            max_upload_size=DEMO_MAX_ZIP_FILESIZE,
            storage=demo_uploads_fs,
            upload_to=mk_upload_to('demo_package.zip'),
            blank=False)

    source_code_url = models.URLField(
            _("Is your source code also available somewhere else on the web (e.g., github)? Please share the link."),
            verify_exists=False, blank=True, null=True)
    license_name = models.CharField(
            _("Select the license that applies to your source code."),
            max_length=64, blank=False, 
            choices=( (x['name'], x['title']) for x in DEMO_LICENSES.values() ))

    creator = models.ForeignKey(User, blank=False, null=True)
    
    created = models.DateTimeField( _('date created'), 
            auto_now_add=True, blank=False)
    modified = models.DateTimeField( _('date last modified'), 
            auto_now=True, blank=False)

    def __unicode__(self):
        return 'Submission "%(title)s"' % dict(
            title=self.title )

    def get_absolute_url(self):
        return reverse('demos.views.detail', kwargs={'slug':self.slug})

    def save(self):
        """Save the submission, updating slug and screenshot thumbnails"""
        self.slug = slugify(self.title)
        super(Submission,self).save()
        self.update_thumbnails()

    def delete(self,using=None):
        root = '%s/%s' % (settings.MEDIA_ROOT, get_root_for_submission(self))
        if isdir(root): rmtree(root)
        super(Submission,self).delete(using)

    def clean(self):
        if self.demo_package:
            Submission.validate_demo_zipfile(self.demo_package)

    def next(self):
        """Find the next submission by created time, return None if not found."""
        try:
            obj = self.get_next_by_created()
            return obj
        except Submission.DoesNotExist:
            return None

    def previous(self):
        """Find the previous submission by created time, return None if not found."""
        try:
            obj = self.get_previous_by_created()
            return obj
        except Submission.DoesNotExist:
            return None

    def thumbnail_url(self, index='1'):
        return getattr(self, 'screenshot_%s' % index).url.replace('screenshot','screenshot_thumb')

    @classmethod
    def allows_listing_hidden_by(cls, user):
        if user.is_staff or user.is_superuser:
            return True
        return False

    def allows_hiding_by(self, user):
        if user.is_staff or user.is_superuser:
            return True
        return False

    def allows_viewing_by(self, user):
        if user.is_staff or user.is_superuser:
            return True
        if user == self.creator:
            return True
        if not self.hidden:
            return True
        return False

    def allows_editing_by(self, user):
        if user.is_staff or user.is_superuser:
            return True
        if user == self.creator:
            return True
        return False

    def allows_deletion_by(self, user):
        if user.is_staff or user.is_superuser:
            return True
        if user == self.creator:
            return True
        return False

    def update_thumbnails(self):
        """Update thumbnails to accompany full-size screenshots"""
        for idx in range(1, 6):

            name = 'screenshot_%s' % idx
            field = getattr(self, name)
            if not field: continue

            try:
                # TODO: Only update thumbnail if source image has changed / is newer
                thumb_name = field.name.replace('screenshot','screenshot_thumb')
                scaled_file = scale_image(field.file, (THUMBNAIL_MAXW, THUMBNAIL_MAXH))
                if scaled_file:
                    field.storage.delete(thumb_name)
                    field.storage.save(thumb_name, scaled_file)
            except:
                # TODO: Had some exceptions here related to scaling that
                # nonetheless resulted in an updated thumbnail. Investigate further.
                pass

    @classmethod
    def get_valid_demo_zipfile_entries(cls, zf):
        """Filter a ZIP file's entries for only accepted entries"""
        # TODO: Should we restrict to a certain set of {css,js,html,wot} extensions?
        return [ x for x in zf.infolist() if 
            not (x.filename.startswith('/') or '/..' in x.filename) and
            not (basename(x.filename).startswith('.')) and
            x.file_size > 0 ]

    @classmethod
    def validate_demo_zipfile(cls, file):
        """Ensure a given file is a valid ZIP file without disallowed file
        entries and with an HTML index."""
        try:
            zf = zipfile.ZipFile(file)
        except:
            raise ValidationError(_('ZIP file contains no acceptable files'))

        if zf.testzip():
            raise ValidationError(_('ZIP file corrupted'))
        
        valid_entries = Submission.get_valid_demo_zipfile_entries(zf) 
        if len(valid_entries) == 0:
            raise ValidationError(_('ZIP file contains no acceptable files'))

        m_mime = magic.Magic(mime=True)

        index_found = False
        for zi in valid_entries:
            name = zi.filename

            # HACK: We're accepting {index,demo}.html as the root index and
            # normalizing on unpack
            if 'index.html' == name or 'demo.html' == name:
                index_found = True

            if zi.file_size > DEMO_MAX_FILESIZE_IN_ZIP:
                raise ValidationError(
                    _('ZIP file contains a file that is too large: %(filename)s') % 
                    { "filename": name }
                )

            file_data = zf.read(zi)
            file_mime_type = m_mime.from_buffer(file_data)

            if file_mime_type in DEMO_MIMETYPE_BLACKLIST:
                raise ValidationError(
                    _('ZIP file contains an unacceptable file: %(filename)s') % 
                    { "filename": name }
                )
        
        if not index_found:
            raise ValidationError(_('HTML index not found in ZIP'))

    def process_demo_package(self):
        """Unpack the demo ZIP file into the appropriate directory, filtering
        out any invalid file entries and normalizing demo.html to index.html if
        present."""

        # Derive a directory name from the zip filename, clean up any existing
        # directory before unpacking.
        new_root_dir = self.demo_package.path.replace('.zip','')
        if isdir(new_root_dir):
            rmtree(new_root_dir)

        # Load up the zip file and extract the valid entries
        zf = zipfile.ZipFile(self.demo_package.file)
        valid_entries = Submission.get_valid_demo_zipfile_entries(zf) 

        for zi in valid_entries:

            # HACK: Normalize demo.html to index.html
            if zi.filename == 'demo.html':
                zi.filename = 'index.html'

            # Relocate all files from detected root dir to a directory named
            # for the zip file in storage
            out_fn = '%s/%s' % ( new_root_dir, zi.filename )
            out_dir = dirname(out_fn)

            # Create parent directories where necessary.
            if not isdir(out_dir):
                makedirs(out_dir, 0775)

            # Extract the file from the zip into the desired location.
            open(out_fn, 'w').write(zf.read(zi))

def update_submission_comment_count(sender, instance, **kwargs):
    """Update the denormalized count of comments for a submission on comment save/delete"""
    obj = instance.content_object
    if isinstance(obj, Submission):
        new_total = ThreadedComment.public.all_for_object(obj).count()  
        Submission.objects.filter(pk=obj.pk).update(comments_total=new_total)
        Submission.objects.invalidate(obj)

models.signals.post_save.connect(update_submission_comment_count, sender=ThreadedComment)
models.signals.post_delete.connect(update_submission_comment_count, sender=ThreadedComment)
