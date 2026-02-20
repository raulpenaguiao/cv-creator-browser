from tests.conftest import register_and_login


def test_list_projects_empty(client):
    register_and_login(client)
    res = client.get('/api/projects')
    assert res.status_code == 200
    assert res.get_json() == []


def test_create_project(client):
    register_and_login(client)
    res = client.post('/api/projects', json={
        'title': 'My App',
        'description': 'A cool app',
        'keywords': 'react, node',
    })
    assert res.status_code == 201

    projects = client.get('/api/projects').get_json()
    assert len(projects) == 1
    assert projects[0]['title'] == 'My App'


def test_create_project_no_title(client):
    register_and_login(client)
    res = client.post('/api/projects', json={'description': 'No title'})
    assert res.status_code == 400


def test_update_project(client):
    register_and_login(client)
    client.post('/api/projects', json={'title': 'Old Title'})
    projects = client.get('/api/projects').get_json()
    proj_id = projects[0]['id']

    res = client.put(f'/api/projects/{proj_id}', json={
        'title': 'New Title',
        'description': 'Updated desc',
    })
    assert res.status_code == 200

    projects = client.get('/api/projects').get_json()
    assert projects[0]['title'] == 'New Title'


def test_delete_project(client):
    register_and_login(client)
    client.post('/api/projects', json={'title': 'To Delete'})
    projects = client.get('/api/projects').get_json()
    proj_id = projects[0]['id']

    res = client.delete(f'/api/projects/{proj_id}')
    assert res.status_code == 200

    assert client.get('/api/projects').get_json() == []


def test_reorder_projects(client):
    register_and_login(client)
    client.post('/api/projects', json={'title': 'A'})
    client.post('/api/projects', json={'title': 'B'})

    projects = client.get('/api/projects').get_json()
    ids = [p['id'] for p in projects]

    res = client.put('/api/projects/reorder', json={'order': list(reversed(ids))})
    assert res.status_code == 200

    projects = client.get('/api/projects').get_json()
    assert projects[0]['title'] == 'B'
