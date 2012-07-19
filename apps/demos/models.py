from hashlib import md5
from datetime import datetime
from time import time, gmtime, strftime
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

from demos import challenge_utils
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

from django.contrib.sites.models import Site
from django.contrib.auth.models import User, AnonymousUser

from taggit.managers import TaggableManager
from taggit_extras.managers import NamespacedTaggableManager
from taggit.models import TaggedItemBase

import south.modelsinspector
south.modelsinspector.add_ignored_fields(["^taggit\.managers"])

from threadedcomments.models import ThreadedComment, FreeThreadedComment

from utils import generate_filename_and_delete_previous

from actioncounters.fields import ActionCounterField

from embedutils import VideoEmbedURLField

from . import scale_image, TAG_DESCRIPTIONS, DEMO_LICENSES

try:
    from PIL import Image
except ImportError:
    import Image


SCREENSHOT_MAXW = getattr(settings, 'DEMO_SCREENSHOT_MAX_WIDTH', 480)
SCREENSHOT_MAXH = getattr(settings, 'DEMO_SCREENSHOT_MAX_HEIGHT', 360)

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
    return '%(h1)s/%(h2)s/%(username)s/%(slug_hash)s' % dict(
         h1=c_name[0], h2=c_name[1], username=c_name, 
         slug_hash=md5(instance.slug).hexdigest())

def mk_upload_to(field_fn):
    """upload_to builder for file upload fields"""
    def upload_to(instance, filename):
        time_now = int(time())
        return '%(base)s/%(time_now)s_%(field_fn)s' % dict( 
            time_now=time_now,
            base=get_root_for_submission(instance), field_fn=field_fn)
    return upload_to

def mk_slug_upload_to(field_fn):
    """upload_to builder for file upload fields, includes slug in filename"""
    def upload_to(instance, filename):
        time_now = int(time())
        return '%(base)s/%(slug_short)s_%(time_now)s_%(field_fn)s' % dict( 
            time_now=time_now, slug_short=instance.slug[:20],
            base=get_root_for_submission(instance), field_fn=field_fn)
    return upload_to



class ReplacingFieldZipFile(FieldFile):

    def delete(self, save=True):
        # Delete any unpacked zip file, if found.
        new_root_dir = self.path.replace('.zip','')
        if isdir(new_root_dir): 
            rmtree(new_root_dir)
        return super(ReplacingFieldZipFile, self).delete(save)

    def save(self, name, content, save=True):
        new_filename = generate_filename_and_delete_previous(self, name)
        super(ReplacingFieldZipFile, self).save(new_filename, content, save)

    def _get_size(self):
        """Override FieldFile size property to return 0 in case of a missing file."""
        try:
            return super(ReplacingFieldZipFile, self)._get_size()
        except OSError, e:
            return 0
    size = property(_get_size)
    

class ReplacingZipFileField(models.FileField):
    # TODO:liberate
    """This field causes an uploaded file to replace an existing one on disk."""
    attr_class = ReplacingFieldZipFile

    def __init__(self, *args, **kwargs):
        self.max_upload_size = kwargs.pop("max_upload_size")
        super(ReplacingZipFileField, self).__init__(*args, **kwargs)

    def clean(self, *args, **kwargs):        
        data = super(ReplacingZipFileField, self).clean(*args, **kwargs)
        
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

south.modelsinspector.add_introspection_rules([
    (
        [ ReplacingZipFileField ],
        [ ],
        {
            'max_upload_size': ['max_upload_size', {'default':5}],
        },
    )
], ["^demos.models.ReplacingZipFileField"])


class ReplacingImageWithThumbFieldFile(ImageFieldFile):
    
    def thumbnail_name(self):
        # HACK: This works, but I'm not proud of it
        if not self.name: return ''
        parts = self.name.rsplit('.', 1)
        return ''.join(( parts[0], '_thumb', '.', parts[1] ))

    def thumbnail_url(self):
        if not self.url: return ''
        # HACK: Use legacy thumbnail URL, if new-style file missing.
        DEV = getattr(settings, 'DEV', False)
        if not DEV and not self.storage.exists(self.thumbnail_name()):
            return self.url.replace('screenshot', 'screenshot_thumb')
        # HACK: This works, but I'm not proud of it
        parts = self.url.rsplit('.', 1)
        return ''.join(( parts[0], '_thumb', '.', parts[1] ))

    def delete(self, save=True):
        # Delete any associated thumbnail image before deleting primary
        t_name = self.thumbnail_name()
        if t_name: 
            self.storage.delete(t_name)
        return super(ImageFieldFile, self).delete(save)

    def save(self, name, content, save=True):
        new_filename = generate_filename_and_delete_previous(self, name)
        super(ImageFieldFile, self).save(new_filename, content, save)

        # Create associated scaled thumbnail image
        t_name = self.thumbnail_name()
        if t_name:
            thumb_file = scale_image(self.storage.open(new_filename), 
                    (self.field.thumb_max_width, self.field.thumb_max_height))
            self.storage.save(t_name, thumb_file)


class ReplacingImageWithThumbField(models.ImageField):
    # TODO:liberate
    """This field causes an uploaded file to replace an existing one on disk."""
    attr_class = ReplacingImageWithThumbFieldFile

    def __init__(self, *args, **kwargs):
        self.full_max_width   = kwargs.pop("full_max_width",  SCREENSHOT_MAXW)
        self.full_max_height  = kwargs.pop("full_max_height",  SCREENSHOT_MAXH)
        self.thumb_max_width  = kwargs.pop("thumb_max_width", THUMBNAIL_MAXW)
        self.thumb_max_height = kwargs.pop("thumb_max_height", THUMBNAIL_MAXH)
        super(ReplacingImageWithThumbField, self).__init__(*args, **kwargs)

    def clean(self, *args, **kwargs):        
        data = super(ReplacingImageWithThumbField, self).clean(*args, **kwargs)
        
        # Scale the input image down to maximum full size.
        scaled_file = scale_image(data.file, 
                (self.full_max_width, self.full_max_height))
        if not scaled_file:
            raise ValidationError(_('Cannot process image'))
        data.file = scaled_file

        return data

south.modelsinspector.add_introspection_rules([
    (
        [ ReplacingImageWithThumbField ],
        [ ],
        {
            'full_max_width': ['full_max_width', {'default':SCREENSHOT_MAXW}],
            'full_max_width': ['full_max_height', {'default':SCREENSHOT_MAXH}],
            'full_max_width': ['full_max_width', {'default':THUMBNAIL_MAXW}],
            'full_max_width': ['thumb_max_height', {'default':THUMBNAIL_MAXH}],
        },
    )
], ["^demos.models.ReplacingImageWithThumbField"])


class SubmissionManager(models.Manager):
    """Manager for Submission objects"""

    def get_by_natural_key(self, slug):
        return self.get(slug=slug)

    # never show censored submissions
    def get_query_set(self):
        return super(SubmissionManager, self).get_query_set().exclude(censored=True)

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
            return queryset.order_by('-likes_recent','-launches_recent')
        else:
            return queryset.order_by('-created')
        

class Submission(models.Model):
    """Representation of a demo submission"""
    objects = SubmissionManager()
    admin_manager = models.Manager()

    title = models.CharField(
            _("what is your demo's name?"), 
            max_length=255, blank=False, unique=True)
    slug = models.SlugField(_("slug"), 
            blank=False, unique=True, max_length=50)
    summary = models.CharField(
            _("describe your demo in one line"),
            max_length=255, blank=False)
    description = models.TextField(
            _("describe your demo in more detail (optional)"), 
            blank=True)

    featured = models.BooleanField()
    hidden = models.BooleanField(
            _("Hide this demo from others?"), default=False)
    censored = models.BooleanField()
    censored_url = models.URLField(
            _("Redirect URL for censorship."),
            verify_exists=False, blank=True, null=True)

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

    taggit_tags = NamespacedTaggableManager(blank=True)

    screenshot_1 = ReplacingImageWithThumbField(
            _('Screenshot #1'),
            max_length=255,
            storage=demo_uploads_fs,
            upload_to=mk_upload_to('screenshot_1.png'), 
            blank=False)
    screenshot_2 = ReplacingImageWithThumbField(
            _('Screenshot #2'),
            max_length=255,
            storage=demo_uploads_fs,
            upload_to=mk_upload_to('screenshot_2.png'), 
            blank=True)
    screenshot_3 = ReplacingImageWithThumbField(
            _('Screenshot #3'),
            max_length=255,
            storage=demo_uploads_fs,
            upload_to=mk_upload_to('screenshot_3.png'), 
            blank=True)
    screenshot_4 = ReplacingImageWithThumbField(
            _('Screenshot #4'),
            max_length=255,
            storage=demo_uploads_fs,
            upload_to=mk_upload_to('screenshot_4.png'), 
            blank=True)
    screenshot_5 = ReplacingImageWithThumbField(
            _('Screenshot #5'),
            max_length=255,
            storage=demo_uploads_fs,
            upload_to=mk_upload_to('screenshot_5.png'), 
            blank=True)

    video_url = VideoEmbedURLField(
            _("have a video of your demo in action? (optional)"),
            verify_exists=False, blank=True, null=True)

    demo_package = ReplacingZipFileField(
            _('select a ZIP file containing your demo'),
            max_length=255,
            max_upload_size=DEMO_MAX_ZIP_FILESIZE,
            storage=demo_uploads_fs,
            upload_to=mk_slug_upload_to('demo_package.zip'),
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

    def natural_key(self):
        return (self.slug,)

    def update(self, **kw):
        """
        Shortcut for doing an UPDATE on this object.

        If _signal=False is in ``kw`` the post_save signal won't be sent.
        """
        signal = kw.pop('_signal', True)
        cls = self.__class__
        using = kw.pop('using', 'default')
        for k, v in kw.items():
            setattr(self, k, v)
        if signal:
            # Detect any attribute changes during pre_save and add those to the
            # update kwargs.
            attrs = dict(self.__dict__)
            models.signals.pre_save.send(sender=cls, instance=self)
            for k, v in self.__dict__.items():
                if attrs[k] != v:
                    kw[k] = v
                    setattr(self, k, v)
        cls.objects.using(using).filter(pk=self.pk).update(**kw)
        if signal:
            models.signals.post_save.send(sender=cls, instance=self,
                                          created=False)

    def __unicode__(self):
        return 'Submission "%(title)s"' % dict(
            title=self.title )

    def get_absolute_url(self):
        return reverse('demos.views.detail', kwargs={'slug':self.slug})

    def _make_unique_slug(self, **kwargs):
        """
        Try to generate a unique 50-character slug.
        
        """
        if self.slug:
            slug = self.slug[:50]
        else:
            slug = slugify(self.title)[:50]
        using = kwargs['using'] if 'using' in kwargs else 'default'
        existing = Submission.objects.using(using).filter(slug=slug)
        if (not existing) or (self.id and self.id in [s.id for s in existing]):
            return slug
        # If the first 50 characters aren't unique, we chop off the
        # last two and try sticking a two-digit number there.
        #
        # If for some reason we get to 100 demos which all have the
        # same first fifty characters in their title, this will
        # break. Hopefully that's unlikely enough that it won't be a
        # problem, but we can always add a check at the end of the
        # while loop or come up with some other method if we actually
        # run into it.
        base_slug = slug[:-2]
        i = 0
        while Submission.objects.filter(slug=slug).exists() and i < 100:
            slug = "%s%02d" % (base_slug, i)
            i += 1
        return slug

    def save(self, **kwargs):
        """Save the submission, updating slug and screenshot thumbnails"""
        self.slug = self._make_unique_slug(**kwargs)
        super(Submission,self).save(**kwargs)

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

    def screenshot_url(self, index='1'):
        """Fetch the screenshot URL for a given index, swallowing errors"""
        try:
            return getattr(self, 'screenshot_%s' % index).url
        except:
            return ''

    def thumbnail_url(self, index='1'):
        """Fetch the screenshot thumbnail URL for a given index, swallowing
        errors"""
        try:
            return getattr(self, 'screenshot_%s' % index).thumbnail_url()
        except:
            return ''

    def get_flags(self):
        """Assemble status flags, based on featured status and a set of special
        tags (eg. for Dev Derby). The flags are assembled in order of display
        priority, so the first flag on the list (if any) is the most
        important"""
        flags = [ ]

        # Iterate through known flags based on tag naming convention. Tag flags
        # are listed here in order of priority.
        tag_flags = ('firstplace', 'secondplace', 'thirdplace', 'finalist')
        for p in tag_flags:
            for tag in self.taggit_tags.all():
                # TODO: Is this 'system:challenge' too hard-codey?
                if tag.name.startswith('system:challenge:%s:' % p):
                    flags.append(p)

        # Featured is an odd-man-out before we had tags
        if self.featured:
            flags.append('featured')

        return flags

    def is_derby_submission(self):
        return bool(self.taggit_tags.all_ns('challenge:'))

    def challenge_closed(self):
        challenge_tags = self.taggit_tags.all_ns('challenge:')
        if not challenge_tags or 'challenge:none' in map(str, challenge_tags):
            return False
        return challenge_utils.challenge_closed(challenge_tags)

    @classmethod
    def allows_listing_hidden_by(cls, user):
        if user.is_staff or user.is_superuser:
            return True
        return False

    def allows_hiding_by(self, user):
        if user.is_staff or user.is_superuser or user == self.creator:
            return True
        return False

    def allows_viewing_by(self, user):
        if not self.censored:
            if user.is_staff or user.is_superuser or user == self.creator:
                return True
            if not self.hidden:
                return True
        return False

    def allows_editing_by(self, user):
        if user.is_staff or user.is_superuser or user == self.creator:
            return True
        return False

    def allows_deletion_by(self, user):
        if user.is_staff or user.is_superuser or user == self.creator:
            return True
        return False

    @classmethod
    def get_valid_demo_zipfile_entries(cls, zf):
        """Filter a ZIP file's entries for only accepted entries"""
        # TODO: Move to zip file field?
        return [ x for x in zf.infolist() if 
            not (x.filename.startswith('/') or '/..' in x.filename) and
            not (basename(x.filename).startswith('.')) and
            x.file_size > 0 ]

    @classmethod
    def validate_demo_zipfile(cls, file):
        """Ensure a given file is a valid ZIP file without disallowed file
        entries and with an HTML index."""
        # TODO: Move to zip file field?
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
            # HACK: Sometimes we get "type; charset", even if charset wasn't asked for
            file_mime_type = m_mime.from_buffer(file_data).split(';')[0]

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
        # TODO: Move to zip file field?

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

models.signals.post_save.connect(update_submission_comment_count, sender=ThreadedComment)
models.signals.post_delete.connect(update_submission_comment_count, sender=ThreadedComment)
