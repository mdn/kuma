import pytest
from pyquery import PyQuery as pq

from kuma.core.urlresolvers import reverse
from kuma.core.utils import to_html
from kuma.wiki.models import Revision

from . import make_test_file
from ..models import Attachment


@pytest.mark.security
def test_xss_file_attachment_title(admin_client, constance_config, root_doc,
                                   wiki_user, editor_client, settings):
    constance_config.WIKI_ATTACHMENT_ALLOWED_TYPES = 'text/plain'

    # use view to create new attachment
    file_for_upload = make_test_file()
    files_url = reverse('attachments.edit_attachment',
                        kwargs={'document_path': root_doc.slug})
    title = '"><img src=x onerror=prompt(navigator.userAgent);>'
    post_data = {
        'title': title,
        'description': 'xss',
        'comment': 'xss',
        'file': file_for_upload,
    }
    response = admin_client.post(files_url, data=post_data,
                                 HTTP_HOST=settings.WIKI_HOST)
    assert response.status_code == 302

    # now stick it in/on a document
    attachment = Attachment.objects.get(title=title)
    content = '<img src="%s" />' % attachment.get_file_url()
    root_doc.current_revision = Revision.objects.create(
        document=root_doc, creator=wiki_user, content=content)

    # view it and verify markup is escaped
    response = editor_client.get(root_doc.get_edit_url(),
                                 HTTP_HOST=settings.WIKI_HOST)
    assert response.status_code == 200
    doc = pq(response.content)
    text = doc('.page-attachments-table .attachment-name-cell').text()
    assert text == ('%s\nxss' % title)
    html = to_html(doc('.page-attachments-table .attachment-name-cell'))
    assert '&gt;&lt;img src=x onerror=prompt(navigator.userAgent);&gt;' in html
    # security bug 1272791
    for script in doc('script'):
        assert title not in script.text_content()
