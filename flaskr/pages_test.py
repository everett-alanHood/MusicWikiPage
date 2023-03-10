from flaskr import create_app
import pytest


# See https://flask.palletsprojects.com/en/2.2.x/testing/ 
# for more info on testing
@pytest.fixture
def app():
    app = create_app({
        'TESTING': True,
    })
    return app

@pytest.fixture
def client(app):
    return app.test_client()

# TODO(Checkpoint (groups of 4 only) Requirement 4): Change test to
# match the changes made in the other Checkpoint Requirements.
def test_home_page(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert b"Music Theory Wiki" in resp.data
    assert b"<h1>" in resp.data

# TODO(Project 1): Write tests for other routes.
def test_auth_login_failed(self,user_blob,user_name,password):
    pass

def test_auth_login_sucesss(self,user_blob,user_name,password):
    pass

def test_logout():
    pass

def test_home():
    pass

def test_pages():
    pass
def test_pages_next():
    pass
def test_about():
    pass
def test_welcome():
    pass

def test_get_login():
    pass

def test_upload():
    pass

def test_get_sign_up_failed():
    pass

def test_get_sign_up_success():
    pass

def test_sign_up_success():
    pass
def test_sign_up_failed():
    pass
