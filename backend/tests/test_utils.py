from app.services.utils import sha256_text


def test_sha256_text_stable():
    assert sha256_text('abc') == sha256_text('abc')
    assert sha256_text('abc') != sha256_text('abcd')
