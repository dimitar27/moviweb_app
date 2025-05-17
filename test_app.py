import pytest
from app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_home_route(client):
    response = client.get('/')
    assert response.status_code == 200
    assert b"Hello" in response.data

def test_users_route(client):
    response = client.get('/users')
    assert response.status_code == 200
    assert b"Users" in response.data

def test_add_user_form(client):
    response = client.get('/add_user')
    assert response.status_code == 200
    assert b"Add New User" in response.data

def test_nonexistent_user(client):
    response = client.get('/users/9999')
    assert response.status_code == 200 or response.status_code == 404

def test_invalid_route(client):
    response = client.get('/thispagedoesnotexist')
    assert response.status_code == 404