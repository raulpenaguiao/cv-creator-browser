from tests.conftest import register_and_login


def test_list_blurbs_empty(client):
    register_and_login(client)
    res = client.get('/api/blurbs?template_name=classic')
    assert res.status_code == 200
    assert res.get_json() == []


def test_generate_no_api_key(client):
    register_and_login(client)
    res = client.post('/api/blurbs/generate', json={
        'field_key': 'professional_summary',
        'template_name': 'classic',
    })
    assert res.status_code == 400
    data = res.get_json()
    assert 'API key' in data['error']


def test_generate_missing_field_key(client):
    register_and_login(client)
    res = client.post('/api/blurbs/generate', json={
        'template_name': 'classic',
    })
    assert res.status_code == 400


def test_update_blurb_nonexistent(client):
    register_and_login(client)
    res = client.put('/api/blurbs/999', json={'status': 'accepted'})
    assert res.status_code == 404


def test_update_blurb_invalid_status(client, app):
    register_and_login(client)
    # Manually insert a blurb for testing
    with app.app_context():
        from app.database import get_db
        db = get_db()
        db.execute(
            'INSERT INTO blurbs (user_id, template_name, field_key, suggestion_text) '
            'VALUES (1, ?, ?, ?)',
            ('classic', 'summary', 'Test suggestion'),
        )
        db.commit()
        row = db.execute('SELECT id FROM blurbs WHERE user_id = 1').fetchone()

    res = client.put(f'/api/blurbs/{row["id"]}', json={'status': 'invalid'})
    assert res.status_code == 400


def test_blurb_crud(client, app):
    register_and_login(client)
    # Manually insert a blurb
    with app.app_context():
        from app.database import get_db
        db = get_db()
        db.execute(
            'INSERT INTO blurbs (user_id, template_name, field_key, suggestion_text) '
            'VALUES (1, ?, ?, ?)',
            ('classic', 'summary', 'A great engineer.'),
        )
        db.commit()

    # List
    res = client.get('/api/blurbs?template_name=classic')
    blurbs = res.get_json()
    assert len(blurbs) == 1
    blurb_id = blurbs[0]['id']

    # Accept
    res = client.put(f'/api/blurbs/{blurb_id}', json={'status': 'accepted'})
    assert res.status_code == 200

    # Modify
    res = client.put(f'/api/blurbs/{blurb_id}', json={
        'status': 'modified',
        'user_text': 'An excellent engineer.',
    })
    assert res.status_code == 200

    # Delete
    res = client.delete(f'/api/blurbs/{blurb_id}')
    assert res.status_code == 200

    blurbs = client.get('/api/blurbs?template_name=classic').get_json()
    assert len(blurbs) == 0
