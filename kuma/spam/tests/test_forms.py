import pytest
from django import forms

from ..constants import CHECK_URL, VERIFY_URL
from ..forms import AkismetCheckFormMixin


class AkismetCheckTestForm(AkismetCheckFormMixin, forms.Form):
    """Test form for checking AkismetCheckFormMixin."""

    def akismet_parameters(self):
        parameters = {
            "blog_lang": "en_us",
            "blog_charset": "UTF-8",
            "comment_author": "testuser",
            "comment_author_email": "testuser@test.com",
            "comment_type": "wiki-revision",
            "user_ip": "0.0.0.0",
            "user_agent": "Mozilla Firefox",
            "referrer": "https://www.netscape.com/",
        }
        parameters.update(self.cleaned_data)
        return parameters


class AkismetContentTestForm(AkismetCheckTestForm):
    """Test form for checking akismet_parameters."""

    content = forms.CharField()


@pytest.fixture
def spam_request(spam_check_everyone, rf):
    """Create a spammy request and setup for spam checking."""
    request = rf.get(
        "/",
        REMOTE_ADDR="0.0.0.0",
        HTTP_USER_AGENT="Mozilla Firefox",
        HTTP_REFERER="https://www.netscape.com/",
    )
    return request


def test_akismet_parameters(constance_config, mock_requests, spam_request):
    """Default AkismetCheckFormMixin.akismet_parameters collects some data."""
    constance_config.AKISMET_KEY = "parameters"
    mock_requests.post(VERIFY_URL, content=b"valid")
    mock_requests.post(CHECK_URL, content=b"false")

    form = AkismetContentTestForm(spam_request, data={"content": "some content"})
    with pytest.raises(AttributeError) as e_info:
        form.akismet_parameters()
    assert str(e_info.value) == (
        "'AkismetContentTestForm' object has no attribute 'cleaned_data'"
    )

    assert form.is_valid()
    assert "content" in form.cleaned_data
    parameters = form.akismet_parameters()
    assert parameters["content"] == "some content"
    # super method called
    assert parameters["user_ip"] == "0.0.0.0"
    assert parameters["user_agent"] == "Mozilla Firefox"
    assert parameters["referrer"] == "https://www.netscape.com/"


@pytest.mark.parametrize("key_set", (True, False))
def test_akismet_key_set(constance_config, mock_requests, spam_request, key_set):
    """Akismet is disabled if the key is unset."""
    constance_config.AKISMET_KEY = "enabled" if key_set else ""
    mock_requests.post(VERIFY_URL, content=b"valid")
    mock_requests.post(CHECK_URL, content=b"true")
    form = AkismetCheckTestForm(spam_request, data={})
    assert form.akismet_enabled() == key_set


def test_akismet_check_ham(constance_config, mock_requests, spam_request):
    """The form is valid if Akismet check returns 'false'."""
    constance_config.AKISMET_KEY = "enabled"
    mock_requests.post(VERIFY_URL, content=b"valid")
    mock_requests.post(CHECK_URL, content=b"false")
    form = AkismetCheckTestForm(spam_request, data={})
    assert form.is_valid()
    assert form.errors == {}


@pytest.mark.parametrize(
    "check_response", (b"true", b"yada yada"), ids=("spam", "error")
)
def test_akismet_check_invalid(
    constance_config, mock_requests, spam_request, check_response
):
    """The form is invalid if Akismet check returns not 'false'."""
    constance_config.AKISMET_KEY = "enabled"
    mock_requests.post(VERIFY_URL, content=b"valid")
    mock_requests.post(CHECK_URL, content=check_response)
    form = AkismetCheckTestForm(spam_request, data={})
    assert not form.is_valid()
    assert form.akismet_error_message in form.errors["__all__"]
    with pytest.raises(forms.ValidationError) as e_info:
        form.akismet_error({})
    assert e_info.value.messages == [form.akismet_error_message]
