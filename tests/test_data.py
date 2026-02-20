import io
import json

from tests.conftest import register_and_login


def test_export_data(client):
    register_and_login(client)
    # Add some data first
    client.put('/api/profile', json={'first_name': 'Jane', 'last_name': 'Doe'})
    client.post('/api/experiences', json={'category': 'work', 'title': 'Dev'})
    client.post('/api/projects', json={'title': 'My Project'})

    res = client.get('/api/data/export')
    assert res.status_code == 200
    data = json.loads(res.data)
    assert data['version'] == 1
    assert data['profile']['first_name'] == 'Jane'
    assert len(data['experiences']) == 1
    assert len(data['projects']) == 1


def test_import_data(client):
    register_and_login(client)

    data = {
        'version': 1,
        'profile': {'first_name': 'Imported', 'last_name': 'User'},
        'experiences': [
            {'category': 'work', 'title': 'Imported Job', 'organization': 'Co'},
        ],
        'projects': [
            {'title': 'Imported Project', 'description': 'Desc'},
        ],
        'settings': {'font_size': 12},
    }

    res = client.post('/api/data/import', data={
        'file': (io.BytesIO(json.dumps(data).encode()), 'data.json'),
    }, content_type='multipart/form-data')
    assert res.status_code == 200

    # Verify imported data
    profile = client.get('/api/profile').get_json()
    assert profile['first_name'] == 'Imported'

    exps = client.get('/api/experiences').get_json()
    assert len(exps) == 1
    assert exps[0]['title'] == 'Imported Job'

    settings = client.get('/api/settings').get_json()
    assert settings['font_size'] == 12


def test_import_invalid_json(client):
    register_and_login(client)
    res = client.post('/api/data/import', data={
        'file': (io.BytesIO(b'not json'), 'data.json'),
    }, content_type='multipart/form-data')
    assert res.status_code == 400


def test_import_invalid_version(client):
    register_and_login(client)
    data = {'version': 99}
    res = client.post('/api/data/import', data={
        'file': (io.BytesIO(json.dumps(data).encode()), 'data.json'),
    }, content_type='multipart/form-data')
    assert res.status_code == 400
