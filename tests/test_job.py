from tests.conftest import register_and_login


def test_list_analyses_empty(client):
    register_and_login(client)
    res = client.get('/api/job/analyses')
    assert res.status_code == 200
    assert res.get_json() == []


def test_analyze_no_api_key(client):
    register_and_login(client)
    res = client.post('/api/job/analyze', json={
        'job_description': 'Software engineer needed with Python experience.',
    })
    # Should fail because no API key set
    assert res.status_code == 400
    data = res.get_json()
    assert 'API key' in data['error']


def test_analyze_empty_description(client):
    register_and_login(client)
    res = client.post('/api/job/analyze', json={'job_description': ''})
    assert res.status_code == 400


def test_delete_analysis_nonexistent(client):
    register_and_login(client)
    res = client.delete('/api/job/analyses/999')
    assert res.status_code == 404
