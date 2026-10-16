import pytest

from app.utils.validators import is_allowed_url

HOSTS = ["youtube.com", "youtu.be"]


@pytest.mark.parametrize(
    "url",
    [
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "https://youtu.be/dQw4w9WgXcQ",
        "https://music.youtube.com/watch?v=abc",
        "http://youtube.com/watch?v=abc",
    ],
)
def test_allowed(url):
    assert is_allowed_url(url, HOSTS)


@pytest.mark.parametrize(
    "url",
    [
        "https://example.com/watch?v=abc",
        "https://evilyoutube.com/watch?v=abc",
        "https://youtube.com.evil.io/watch?v=abc",
        "ftp://youtube.com/video",
        "not a url",
        "file:///etc/passwd",
    ],
)
def test_rejected(url):
    assert not is_allowed_url(url, HOSTS)
