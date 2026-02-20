from tests.conftest import register_and_login


def test_download_pdf_no_compile(client):
    register_and_login(client)
    res = client.get('/api/generate/download/pdf')
    assert res.status_code == 404


def test_download_tex_no_compile(client):
    register_and_login(client)
    res = client.get('/api/generate/download/tex')
    assert res.status_code == 404
