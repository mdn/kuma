import datetime
import json
from pathlib import Path

from django.conf import settings
from django.http import HttpResponseNotFound
from django.shortcuts import redirect

from .utils import (
    convert_to_http_date,
    full_attachment_url,
    full_mindtouch_attachment_url,
)

# In the olden days of Kuma, we used to have people upload files into the Wiki.
# These are called Attachments.
# Later we realized it's bad to host these files on disk so we uploaded them
# all into S3 and in the Django view, we simply redirected to the public
# S3 URL. E.g.
# GET /files/16014/LeagueMonoVariable.ttf
#  ==> 301 https://media.prod.mdn.mozit.cloud/attachments/2018/06/05/16014/96e6cc293bd18f32a17371500d01301b/LeagueMonoVariable.ttf
#
# Now, you can't upload files any more but we have these absolute URLs
# peppered throughout the translated-content since we moved to Yari. Cleaning
# all of that up is considered too hard so it's best to just keep serving the
# redirects.
# But in an effort to seriously simplify and be able to clean up a much of
# MySQL data, we decided to scrape all the legacy file attachments mentioned
# through out all mdn/content and mdn/translated-content. We then looked up
# each URL's final destination URL. All of these we dumped into the
# file called 'redirects.json' which is stored here on disk in this folder.
# Now the view function just needs to reference that mapping. If something's
# not in the mapping it's either a fumbly typo or it's simple a file attachment
# URL not used anywhere in the content or translated-content.

REDIRECTS_FILE = Path(__file__).parent / "redirects.json"
assert REDIRECTS_FILE.exists(), REDIRECTS_FILE
with open(REDIRECTS_FILE) as f:
    _redirects = json.load(f)
    assert _redirects

# The mindtouch_redirects.json file is for URLs like /@api/deki/files/5695/=alpha.png
# and the json file points to the final destination on S3.

MINDTOUCH_REDIRECTS_FILE = Path(__file__).parent / "mindtouch_redirects.json"
assert MINDTOUCH_REDIRECTS_FILE.exists(), MINDTOUCH_REDIRECTS_FILE
with open(MINDTOUCH_REDIRECTS_FILE) as f:
    _mindtouch_redirects = json.load(f)
    assert _mindtouch_redirects


def raw_file(request, attachment_id, filename):
    """
    Serve up an attachment's file.
    """
    if attachment_id not in _redirects:
        return HttpResponseNotFound(f"{attachment_id} not a known redirect")

    if settings.DOMAIN in request.get_host():
        file_url = full_attachment_url(attachment_id, filename)
        return redirect(file_url, permanent=True)

    return _redirect_final_path(_redirects[attachment_id])


def mindtouch_file_redirect(request, file_id, filename):
    """Redirect an old MindTouch file URL to a new kuma file URL."""
    if file_id not in _mindtouch_redirects:
        return HttpResponseNotFound(f"{file_id} not a known redirect")

    if settings.DOMAIN in request.get_host():
        file_url = full_mindtouch_attachment_url(file_id, filename)
        return redirect(file_url, permanent=True)

    return _redirect_final_path(_mindtouch_redirects[file_id])


def _redirect_final_path(final_path):
    assert settings.ATTACHMENTS_AWS_S3_CUSTOM_DOMAIN
    redirect_url = "https://" if settings.ATTACHMENTS_AWS_S3_SECURE_URLS else "http://"
    redirect_url += settings.ATTACHMENTS_AWS_S3_CUSTOM_DOMAIN
    redirect_url += final_path
    response = redirect(redirect_url)

    olden = datetime.datetime.now() - datetime.timedelta(days=365)
    response["Last-Modified"] = convert_to_http_date(olden)
    response["X-Frame-Options"] = f"ALLOW-FROM {settings.DOMAIN}"
    return response
