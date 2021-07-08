import json
from pathlib import Path

import pytest


@pytest.fixture
def sample_attachment_redirect():
    redirects_file = Path(__file__).parent.parent / "redirects.json"
    with open(redirects_file) as f:
        redirects = json.load(f)
    first = list(redirects.keys())[0]
    return {"id": int(first), "url": redirects[first]}


@pytest.fixture
def sample_mindtouch_attachment_redirect():
    redirects_file = Path(__file__).parent.parent / "mindtouch_redirects.json"
    with open(redirects_file) as f:
        redirects = json.load(f)
    first = list(redirects.keys())[0]
    return {"id": int(first), "url": redirects[first]}
