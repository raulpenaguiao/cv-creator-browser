import pytest


@pytest.fixture
def sanitize():
    from app.services.latex_service import sanitize_latex
    return sanitize_latex


def test_empty_string(sanitize):
    assert sanitize('') == ''
    assert sanitize(None) == ''


def test_plain_text(sanitize):
    assert sanitize('Hello World') == 'Hello World'


def test_ampersand(sanitize):
    assert sanitize('A & B') == r'A \& B'


def test_percent(sanitize):
    assert sanitize('100%') == r'100\%'


def test_dollar(sanitize):
    assert sanitize('$100') == r'\$100'


def test_hash(sanitize):
    assert sanitize('#1') == r'\#1'


def test_underscore(sanitize):
    assert sanitize('my_var') == r'my\_var'


def test_braces(sanitize):
    assert sanitize('{test}') == r'\{test\}'


def test_tilde(sanitize):
    assert sanitize('~') == r'\textasciitilde{}'


def test_caret(sanitize):
    assert sanitize('^') == r'\textasciicircum{}'


def test_backslash(sanitize):
    assert sanitize('\\') == r'\textbackslash{}'


def test_multiple_specials(sanitize):
    result = sanitize('$100 & 50%')
    assert r'\$' in result
    assert r'\&' in result
    assert r'\%' in result


def test_no_double_escape_backslash(sanitize):
    # Ensure backslash is not double-escaped
    result = sanitize('\\test')
    assert r'\textbackslash{}' in result
    assert r'\textbackslash{}\textbackslash{}' not in result
