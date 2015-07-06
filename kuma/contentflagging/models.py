"""Models for content moderation flagging"""
from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core import urlresolvers
from django.core.mail import send_mail
from django.db import models
from django.template import Context, loader
from django.utils.translation import ugettext_lazy as _

from kuma.core.utils import get_unique


FLAG_REASONS = getattr(settings, "FLAG_REASONS", (
    ('notworking', _('This is not working for me')),
    ('inappropriate', _('This contains inappropriate content')),
    ('plagarised', _('This was not created by the author')),
    ('fakeauthor', _('The author is fake')),
))

FLAG_STATUS_FLAGGED = "flagged"
FLAG_STATUS_REJECTED = "rejected"
FLAG_STATUS_NOTIFIED = "notified"
FLAG_STATUS_HIDDEN = "hidden"
FLAG_STATUS_DELETED = "deleted"

FLAG_STATUSES = getattr(settings, "FLAG_STATUSES", (
    (FLAG_STATUS_FLAGGED, _("Flagged")),
    (FLAG_STATUS_REJECTED, _("Flag rejected by moderator")),
    (FLAG_STATUS_NOTIFIED, _("Creator notified")),
    (FLAG_STATUS_HIDDEN, _("Content hidden by moderator")),
    (FLAG_STATUS_DELETED, _("Content deleted by moderator")),
))

FLAG_NOTIFICATIONS = {}
for reason in FLAG_REASONS:
    FLAG_NOTIFICATIONS[reason[0]] = True
# to refine flag notifications, change preceding line to False and add
# individual reasons to the set like so:
# FLAG_NOTIFICATIONS['inappropriate'] = True


class ContentFlagManager(models.Manager):
    """Manager for ContentFlags"""

    def flag(self, request, object, flag_type, explanation, recipients=None):
        """Create a flag for a content item, if the unique request hasn't
        already done so before."""
        if flag_type not in dict(FLAG_REASONS):
            return (None, False)

        content_type = ContentType.objects.get_for_model(object)
        user, ip, user_agent, unique_hash = get_unique(content_type, object.pk,
                                                       request=request)

        defaults = dict(content_type=content_type,
                        object_pk=object.pk, ip=ip,
                        user_agent=user_agent, user=user,
                        flag_type=flag_type,
                        explanation=explanation)
        cf = ContentFlag.objects.get_or_create(unique_hash=unique_hash,
                                               defaults=defaults)

        if recipients:
            subject = _("{object} Flagged")
            subject = subject.format(object=object)
            t = loader.get_template('contentflagging/email/flagged.ltxt')
            url = '/admin/contentflagging/contentflag/' + str(object.pk)
            content = t.render(Context({'url': url,
                                        'object': object,
                                        'flag_type': flag_type}))
            send_mail(subject, content,
                      settings.DEFAULT_FROM_EMAIL, recipients)
        return cf

    def flags_by_type(self, status=FLAG_STATUS_FLAGGED):
        """Return a dict of flags by content type."""
        flags = (self.filter(flag_status=status)
                     .prefetch_related('content_object'))
        flag_dict = {}
        for flag in flags:
            model_class = flag.content_type.model_class()
            model_name = model_class._meta.verbose_name_plural
            if model_name not in flag_dict:
                flag_dict[model_name] = []
            flag_dict[model_name].append(flag)
        return flag_dict


class ContentFlag(models.Model):
    """Moderation flag submitted against a content item"""
    objects = ContentFlagManager()

    class Meta:
        ordering = ('-created',)
        get_latest_by = 'created'

    flag_status = models.CharField(_('current status of flag review'),
                                   max_length=16, blank=False,
                                   choices=FLAG_STATUSES, default='flagged')
    flag_type = models.CharField(_('reason for flagging the content'),
                                 max_length=64, db_index=True,
                                 blank=False, choices=FLAG_REASONS)
    explanation = models.TextField(_('please explain what content you '
                                     'feel is inappropriate'),
                                   max_length=255, blank=True)

    content_type = models.ForeignKey(ContentType, editable=False,
                                     verbose_name="content type",
                                     related_name="content_type_set_for_%(class)s",)
    object_pk = models.CharField(_('object ID'), max_length=32, editable=False)
    content_object = GenericForeignKey('content_type', 'object_pk')

    ip = models.CharField(max_length=40, editable=False, blank=True, null=True)
    user_agent = models.CharField(max_length=128, editable=False,
                                  blank=True, null=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, editable=False,
                             blank=True, null=True)

    # HACK: As it turns out, MySQL doesn't consider two rows with NULL values
    # in a column as duplicates. So, resorting to calculating a unique hash in
    # code.
    unique_hash = models.CharField(max_length=32, editable=False,
                                   unique=True, db_index=True, null=True)

    created = models.DateTimeField(_('date submitted'), auto_now_add=True,
                                   blank=False, editable=False)
    modified = models.DateTimeField(_('date last modified'),
                                    auto_now=True, blank=False)

    def __unicode__(self):
        return ('ContentFlag %(flag_type)s -> "%(title)s"' % dict(
                flag_type=self.flag_type, title=str(self.content_object)))

    def save(self, *args, **kwargs):
        # Ensure unique_hash is updated whenever the object is saved
        user, ip, user_agent, unique_hash = get_unique(
            self.content_type, self.object_pk,
            ip=self.ip, user_agent=self.user_agent, user=self.user)
        self.unique_hash = unique_hash
        super(ContentFlag, self).save(*args, **kwargs)

    def content_view_link(self):
        """HTML link to the absolute URL for the linked content object"""
        object = self.content_object
        return ('<a target="_new" href="%(link)s">View %(title)s</a>' %
                dict(link=object.get_absolute_url(), title=object))
    content_view_link.allow_tags = True

    def content_admin_link(self):
        """HTML link to the admin page for the linked content object"""
        object = self.content_object
        ct = ContentType.objects.get_for_model(object)
        url_name = 'admin:%(app)s_%(model)s_change' % dict(
            app=ct.app_label, model=ct.model)
        link = urlresolvers.reverse(url_name, args=(object.id,))
        return ('<a target="_new" href="%(link)s">Edit %(title)s</a>' %
                dict(link=link, title=object))
    content_admin_link.allow_tags = True
