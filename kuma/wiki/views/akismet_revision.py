import json

from django.contrib.auth.decorators import permission_required
from django.http import HttpResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from kuma.core.utils import format_date_time
from kuma.wiki.forms import RevisionAkismetSubmissionSpamForm
from kuma.wiki.models import RevisionAkismetSubmission


@csrf_exempt
@require_POST
@permission_required('wiki.add_revisionakismetsubmission')
def submit_akismet_spam(request):
    """
    Creates SPAM Akismet record for revision.
    Return json object with Akismet Record data.

    TODO: Create Submitting as HAM record for revision
    """

    submission = RevisionAkismetSubmission(sender=request.user, type="spam")
    data = RevisionAkismetSubmissionSpamForm(data=request.POST, instance=submission, request=request)

    if data.is_valid():
        data.save()

        revision = data.cleaned_data['revision']
        akismet_revisions = (RevisionAkismetSubmission.objects.filter(revision=revision)
                                                              .order_by('id')
                                                              .values('sender__username', 'sent', 'type'))

        data = [
            {
                "sender": rev["sender__username"],
                "sent": format_date_time(value=rev["sent"],
                                         format='datetime', request=request)[0],
                "type": rev["type"]}
            for rev in akismet_revisions]

        return HttpResponse(json.dumps(data, sort_keys=True),
                            content_type='application/json; charset=utf-8', status=201)

    return HttpResponseBadRequest()
