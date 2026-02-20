from tests.conftest import register_and_login


def test_get_profile_unauthenticated(client):
    res = client.get('/api/profile')
    assert res.status_code == 401


def test_get_profile_empty(client):
    register_and_login(client)
    res = client.get('/api/profile')
    assert res.status_code == 200
    data = res.get_json()
    assert data['first_name'] == ''


def test_update_profile(client):
    register_and_login(client)
    res = client.put('/api/profile', json={
        'first_name': 'John',
        'last_name': 'Doe',
        'email_contact': 'john@example.com',
        'phone': '+1234567890',
        'address': '123 Main St',
        'linkedin': 'https://linkedin.com/in/johndoe',
        'website': 'https://johndoe.com',
        'bio': 'A software engineer.',
    })
    assert res.status_code == 200

    res = client.get('/api/profile')
    data = res.get_json()
    assert data['first_name'] == 'John'
    assert data['last_name'] == 'Doe'
    assert data['bio'] == 'A software engineer.'
