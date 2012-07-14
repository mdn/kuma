import logging
from optparse import make_option

from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand
from django.db.utils import IntegrityError
from django.db.models.signals import post_save, post_delete
from django.forms.models import model_to_dict

from taggit.models import Tag, TaggedItem
from threadedcomments.models import ThreadedComment

from actioncounters.models import ActionCounterUnique
from demos.models import Submission, update_submission_comment_count
from devmo.models import UserProfile


logger = logging.getLogger(__name__)


class Command(BaseCommand):

    option_list = BaseCommand.option_list + (
        make_option('--slug', dest="slug", default=None,
                    help="Migrate specific demo by slug"),
        make_option('--skip-actions', action="store_true",
                    dest="skip_actions", default=False,
                    help="Skip migrating individual action records"),
    )

    def handle(self, *fixture_labels, **options):
        if options['slug']:
            source_demos = Submission.objects.filter(slug=options['slug'])
        else:
            source_demos = Submission.objects.all()
        logger.info("Migrating %s demo(s)" % len(source_demos))
        for source_demo in source_demos:
            destination_demo = _get_or_create_destination_demo(source_demo)
            destination_creator = _get_or_create_destination_creator(
                source_demo)

            destination_demo.creator = destination_creator
            destination_demo = _update_fields(destination_demo, source_demo)
            destination_demo.save(using='new')

            _delete_and_recreate_tags(source_demo, destination_demo)

            _delete_and_recreate_comments(source_demo, destination_demo)

            if not options['skip_actions']:
                _delete_and_recreate_action_counters(source_demo,
                                                     destination_demo)


def _delete_and_recreate_tags(source_demo, destination_demo):
    source_type, destination_type = _get_demo_content_types()

    source_tags = source_demo.taggit_tags.all()
    source_tags_names = [tag.name for tag in source_tags]
    destination_tags = destination_demo.taggit_tags.using('new').all()
    destination_tags_names = [tag.name for tag in destination_tags]

    if source_tags_names == destination_tags_names:
        return destination_tags
    else:
        destination_tags.delete()
        logger.info("%s: Migrating %s tag(s): %s" % (source_demo.slug,
                                                    len(source_tags),
                                                  source_tags_names))
        for source_tag in source_tags:
            destination_tag = (
                Tag.objects.using('new').get(slug=source_tag.slug))
            destination_demo_tag = TaggedItem.objects.create(
                content_type=destination_type,
                object_id=destination_demo.id,
                tag = destination_tag)
            destination_demo_tag.save(using='new')
    return destination_tags


def _delete_and_recreate_comments(source_demo, destination_demo):
    source_type, destination_type = _get_demo_content_types()
    # delete destination comments
    ThreadedComment.objects.using('new').filter(
                            content_type=destination_type,
                            object_id=destination_demo.id).delete()

    # disconnect update comment count - we already migrate the comments_total
    # value during _update_fields
    # http://stackoverflow.com/q/2209159/571420
    def disconnect_signal(signal, receiver, sender):
        disconnect = getattr(signal, 'disconnect')
        disconnect(receiver, sender)

    disconnect_signal(post_save, update_submission_comment_count,
                                                            ThreadedComment)
    disconnect_signal(post_delete, update_submission_comment_count,
                                                            ThreadedComment)

    source_comments = ThreadedComment.objects.filter(content_type=source_type,
                                                     object_id=source_demo.id)
    logger.info("%s: Migrating %s comment(s)" % (source_demo.slug,
                                               len(source_comments)))
    for comment in source_comments:
        comment.pk = None
        comment.content_type = destination_type
        comment.object_id = destination_demo.id
        comment.user = _get_or_create_destination_commentor(source_demo,
                                                            comment)
        try:
            comment.save(using='new')
        except:
            logger.warning("%s: Couldn't save %s's comment." %
                           (destination_demo.slug, comment.user.username))


def _get_demo_content_types():
    source_type = ContentType.objects.get_by_natural_key('demos', 'submission')
    # have to use .get because QuerySet returned by using() isn't a manager
    # with get_natural_key (django bug?)
    destination_type = ContentType.objects.using('new').get(
        app_label='demos', model='submission')
    return source_type, destination_type


def _delete_and_recreate_action_counters(source_demo, destination_demo):
    source_type, destination_type = _get_demo_content_types()
    # delete destination action counters
    ActionCounterUnique.objects.using('new').filter(
                            content_type=destination_type,
                            object_pk=destination_demo.id).delete()

    # copy source action counters to destination
    source_actions = ActionCounterUnique.objects.filter(
                                content_type=source_type,
                                object_pk=source_demo.id)
    logger.info("%s: Migrating %s action(s)" % (source_demo.slug,
                                              len(source_actions)))
    for action in source_actions:
        action.pk = None
        action.content_type = destination_type
        action.object_pk = destination_demo.pk
        try:
            action.save(using='new')
        except IntegrityError:
            logger.warning("%s: Couldn't save %s action." %
                           (destination_demo.slug, action.name))


def _get_or_create_destination_demo(source_demo):
    try:
        destination_demo = Submission.objects.using('new').get(
            slug=source_demo.slug)
        logger.info("%s: exists" % source_demo.slug)
    except Submission.DoesNotExist:
        destination_demo = source_demo
        destination_demo.pk = None
        logger.info("%s: created" % source_demo.slug)
    return destination_demo


def _get_or_create_destination_creator(source_demo):
    try:
        destination_creator = User.objects.using('new').get(
            username=source_demo.creator.username)
        logger.info("%s: Creator %s exists, id: %s" % (
                                                source_demo.slug,
                                                destination_creator.username,
                                                destination_creator.id))
    except User.DoesNotExist:
        destination_creator = source_demo.creator
        destination_creator.pk = None
        destination_creator.save(using='new')
        logger.info("%s: Creator %s created, id: %s" % (
                                                source_demo.slug,
                                                destination_creator.username,
                                                destination_creator.id))
    _get_or_create_destination_profile(source_demo, destination_creator)
    return destination_creator


def _get_or_create_destination_commentor(source_demo, source_comment):
    try:
        destination_commentator = User.objects.using('new').get(
            username=source_comment.user.username)
        logger.info("%s: Commentator %s exists, id: %s" % (
                                            source_demo.slug,
                                            destination_commentator.username,
                                            destination_commentator.id))
    except User.DoesNotExist:
        destination_commentator = source_comment.user
        destination_commentator.pk = None
        destination_commentator.save(using='new')
        logger.info("%s: Commentator %s created, id: %s" % (
                                            source_demo.slug,
                                            destination_commentator.username,
                                            destination_commentator.id))
    _get_or_create_destination_profile(source_demo, destination_commentator)
    return destination_commentator


def _get_or_create_destination_profile(source_demo, destination_user):
    try:
        destination_profile = UserProfile.objects.using('new').get(
            user=destination_user)
        logger.info("%s: UserProfile %s exists, id: %s" % (
                                            source_demo.slug,
                                            destination_user.username,
                                            destination_user.id))
    except UserProfile.DoesNotExist:
        source_profile = UserProfile.objects.get(user=source_demo.creator)
        destination_profile = source_profile
        destination_profile.pk = None
        destination_profile.user = destination_user
        destination_profile.save(using='new')
        logger.info("%s: Profile %s created, id: %s" % (
                                            source_demo.slug,
                                            destination_user.username,
                                            destination_user.id))
    return destination_profile


def _update_fields(existing_demo, updating_demo):
    exclude_fields = ['id', 'creator', 'taggit_tags']
    update_dict = model_to_dict(updating_demo, exclude=exclude_fields)
    update_dict['using'] = 'new'
    existing_demo.update(**dict(update_dict))
    return existing_demo
