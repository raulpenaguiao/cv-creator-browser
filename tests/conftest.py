import pytest

from app import create_app
from app.database import get_db, init_test_db
from config import TestConfig


@pytest.fixture
def app():
    app = create_app(TestConfig)

    with app.app_context():
        init_test_db()
        yield app


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def db(app):
    with app.app_context():
        yield get_db()


def register_user(client, username='testuser', email='test@example.com'):
    return client.post('/api/auth/register', json={
        'username': username,
        'email': email,
    })


def login_user(client, username='testuser', password=None):
    return client.post('/api/auth/login', json={
        'username': username,
        'password': password,
    })


def register_and_login(client, username='testuser', email='test@example.com'):
    res = register_user(client, username, email)
    data = res.get_json()
    password = data['password']
    login_user(client, username, password)
    return password
