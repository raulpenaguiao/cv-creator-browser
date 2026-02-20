from tests.conftest import register_and_login


def test_get_settings(client):
    register_and_login(client)
    res = client.get('/api/settings')
    assert res.status_code == 200
    data = res.get_json()
    assert data['openai_api_key_set'] is False
    assert data['selected_template'] == 'classic'
    assert data['sentences_per_field'] == 3
    assert data['font_size'] == 11


def test_update_settings(client):
    register_and_login(client)
    res = client.put('/api/settings', json={
        'selected_template': 'classic',
        'sentences_per_field': 5,
        'font_size': 12,
    })
    assert res.status_code == 200

    data = client.get('/api/settings').get_json()
    assert data['sentences_per_field'] == 5
    assert data['font_size'] == 12


def test_set_api_key(client):
    register_and_login(client)
    res = client.put('/api/settings', json={
        'openai_api_key': 'sk-test-key-12345',
    })
    assert res.status_code == 200

    data = client.get('/api/settings').get_json()
    assert data['openai_api_key_set'] is True
    # Key should never be returned
    assert 'openai_api_key' not in data
    assert 'openai_api_key_enc' not in data


def test_settings_clamp_values(client):
    register_and_login(client)
    client.put('/api/settings', json={
        'sentences_per_field': 99,
        'font_size': 2,
    })
    data = client.get('/api/settings').get_json()
    assert data['sentences_per_field'] == 10  # clamped to max
    assert data['font_size'] == 8  # clamped to min


def test_list_templates(client):
    register_and_login(client)
    res = client.get('/api/settings/templates')
    assert res.status_code == 200
    data = res.get_json()
    assert 'templates' in data
    assert len(data['templates']) >= 1
    assert data['templates'][0]['name'] == 'classic'
