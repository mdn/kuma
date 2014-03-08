from django.db.models.signals import post_save

import waffle

from badger.utils import get_badge

from wiki.models import Revision


# Machine-awarded badges defined here
badges = [
    dict(slug="welcome",
         title="Welcome to MDN",
         description="You are a new user on MDN!"),
    dict(slug="learner",
         title="Learner!",
         description="You are a learner!"),
    dict(slug="first-document",
         title="First document!",
         description="You've written your first MDN document!"),
    dict(slug="first-edit",
         title="First edit!",
         description="You've made your first edit to an MDN document!"),
    dict(slug="fifth-edit",
         title="Fifth edit!",
         description="You're really coming along now as an editor!"),
    dict(slug="dev-derbier",
         title="Dev Derbier",
         description="Welcome to the Dev Derby!"),
]


# Middleware to award badges based on site activity
class BadgeAwardingMiddleware(object):

    def process_request(self, request):
        if not waffle.flag_is_active(request, 'badger'):
            return None
        if not hasattr(request, 'user'):
            return None
        if not request.user.is_authenticated():
            return None

        b_learner = get_badge('learner')
        if ('/learn' in request.path and
                not b_learner.is_awarded_to(request.user)):
            b_learner.award_to(request.user)

        b_dev_derbier = get_badge('dev-derbier')
        if ('/demos/devderby' in request.path and
                not b_dev_derbier.is_awarded_to(request.user)):
            b_dev_derbier.award_to(request.user)

        return None


# Register model signals to award badges in reaction to model activity.
def register_signals():
    post_save.connect(on_revision_save, sender=Revision)


def on_revision_save(sender, **kwargs):
    if not waffle.switch_is_active('badger'):
        return

    o = kwargs['instance']
    created = kwargs['created']

    # Reward the first revision of a new document
    first_document = get_badge('first-document')
    if not first_document.is_awarded_to(o.creator):
        if o.document.revisions.count() == 1:
            first_document.award_to(o.creator)

    # Reward the first edit of any document
    first_edit = get_badge('first-edit')
    if not first_edit.is_awarded_to(o.creator):
        first_edit.award_to(o.creator)

    # Reward the fifth revision
    fifth_edit = get_badge('fifth-edit')
    if not fifth_edit.is_awarded_to(o.creator):
        p = fifth_edit.progress_for(o.creator).increment_by(1)
        if p.counter >= 5:
            fifth_edit.award_to(o.creator)
            p.delete()
