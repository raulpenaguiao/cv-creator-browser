from tests.conftest import login_user, register_and_login, register_user


def test_session_unauthenticated(client):
    res = client.get('/api/auth/session')
    assert res.status_code == 200
    data = res.get_json()
    assert data['authenticated'] is False


def test_register(client):
    res = register_user(client)
    assert res.status_code == 201
    data = res.get_json()
    assert 'password' in data
    assert len(data['password']) > 8
    assert data['username'] == 'testuser'


def test_register_duplicate_username(client):
    register_user(client)
    res = register_user(client, username='testuser', email='other@example.com')
    assert res.status_code == 409


def test_register_duplicate_email(client):
    register_user(client)
    res = register_user(client, username='otheruser', email='test@example.com')
    assert res.status_code == 409


def test_register_missing_fields(client):
    res = client.post('/api/auth/register', json={'username': ''})
    assert res.status_code == 400


def test_register_short_username(client):
    res = client.post('/api/auth/register', json={'username': 'ab', 'email': 'a@b.com'})
    assert res.status_code == 400


def test_login_success(client):
    res = register_user(client)
    password = res.get_json()['password']

    res = login_user(client, password=password)
    assert res.status_code == 200
    data = res.get_json()
    assert data['user']['username'] == 'testuser'


def test_login_wrong_password(client):
    register_user(client)
    res = login_user(client, password='wrongpassword')
    assert res.status_code == 401


def test_login_nonexistent_user(client):
    res = login_user(client, username='nobody', password='pass')
    assert res.status_code == 401


def test_session_authenticated(client):
    register_and_login(client)
    res = client.get('/api/auth/session')
    data = res.get_json()
    assert data['authenticated'] is True
    assert data['user']['username'] == 'testuser'


def test_logout(client):
    register_and_login(client)
    res = client.post('/api/auth/logout')
    assert res.status_code == 200

    res = client.get('/api/auth/session')
    data = res.get_json()
    assert data['authenticated'] is False


def test_reset_request_always_success(client):
    # Should return success even for non-existent email (no enumeration)
    res = client.post('/api/auth/reset-request', json={'email': 'nobody@example.com'})
    assert res.status_code == 200


def test_reset_confirm_invalid_token(client):
    res = client.post('/api/auth/reset-confirm', json={'token': 'invalidtoken'})
    assert res.status_code == 400


def test_reset_flow(client, app):
    register_user(client)

    # Request reset
    res = client.post('/api/auth/reset-request', json={'email': 'test@example.com'})
    assert res.status_code == 200

    # Get the token from the DB directly
    with app.app_context():
        from app.database import get_db
        db = get_db()
        row = db.execute('SELECT * FROM password_reset_tokens ORDER BY id DESC LIMIT 1').fetchone()
        assert row is not None

    # We can't easily get the raw token from the hash, so test via the service directly
    from app.services.auth_service import create_reset_token, validate_reset_token
    with app.app_context():
        from app.models import User
        user = User.get_by_username('testuser')
        token = create_reset_token(user.id)
        new_password = validate_reset_token(token)
        assert new_password is not None
        assert len(new_password) > 8

        # Token should be single-use
        assert validate_reset_token(token) is None
