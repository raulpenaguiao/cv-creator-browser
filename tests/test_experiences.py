from tests.conftest import register_and_login


def test_list_experiences_empty(client):
    register_and_login(client)
    res = client.get('/api/experiences')
    assert res.status_code == 200
    assert res.get_json() == []


def test_create_experience(client):
    register_and_login(client)
    res = client.post('/api/experiences', json={
        'category': 'work',
        'title': 'Software Engineer',
        'organization': 'Acme Corp',
        'start_date': 'Jan 2020',
        'end_date': 'Present',
        'description': 'Built stuff.',
        'keywords': 'python, flask',
    })
    assert res.status_code == 201

    res = client.get('/api/experiences')
    data = res.get_json()
    assert len(data) == 1
    assert data[0]['title'] == 'Software Engineer'
    assert data[0]['category'] == 'work'


def test_create_experience_invalid_category(client):
    register_and_login(client)
    res = client.post('/api/experiences', json={
        'category': 'invalid',
        'title': 'Test',
    })
    assert res.status_code == 400


def test_update_experience(client):
    register_and_login(client)
    client.post('/api/experiences', json={
        'category': 'work',
        'title': 'Dev',
    })
    exps = client.get('/api/experiences').get_json()
    exp_id = exps[0]['id']

    res = client.put(f'/api/experiences/{exp_id}', json={
        'category': 'education',
        'title': 'CS Degree',
        'organization': 'MIT',
    })
    assert res.status_code == 200

    exps = client.get('/api/experiences').get_json()
    assert exps[0]['title'] == 'CS Degree'
    assert exps[0]['category'] == 'education'


def test_delete_experience(client):
    register_and_login(client)
    client.post('/api/experiences', json={'category': 'work', 'title': 'Dev'})
    exps = client.get('/api/experiences').get_json()
    exp_id = exps[0]['id']

    res = client.delete(f'/api/experiences/{exp_id}')
    assert res.status_code == 200

    exps = client.get('/api/experiences').get_json()
    assert len(exps) == 0


def test_delete_nonexistent_experience(client):
    register_and_login(client)
    res = client.delete('/api/experiences/999')
    assert res.status_code == 404


def test_reorder_experiences(client):
    register_and_login(client)
    client.post('/api/experiences', json={'category': 'work', 'title': 'First'})
    client.post('/api/experiences', json={'category': 'work', 'title': 'Second'})

    exps = client.get('/api/experiences').get_json()
    ids = [e['id'] for e in exps]

    # Reverse order
    res = client.put('/api/experiences/reorder', json={'order': list(reversed(ids))})
    assert res.status_code == 200

    exps = client.get('/api/experiences').get_json()
    assert exps[0]['title'] == 'Second'
