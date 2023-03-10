from flaskr import create_app
from unittest.mock import patch
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
    assert resp.status_code == 200 #This check that the connection to homepage is good
    assert b"Music Theory Wiki" in resp.data #This check if the cilent can grabs the data within the homepage
    assert b"<h1>" in resp.data

# TODO(Project 1): Write tests for other routes.
def test_auth_login_failed(self,user_blob,user_name,password):
    pass

def test_auth_login_sucesss(self,user_blob,user_name,password):
    pass

def test_logout():
    pass
def test_pages():
    pass
def test_pages_next():
    pass
def test_sign_up_success():
    pass
def test_sign_up_failed():
    pass
def test_upload_failed(client):
    resp=client.get("/upload")
    assert resp.status_code ==200 #This check that the connection to upload is good
    
def test_upload_success(client):
    resp=client.get("/upload")
    assert resp.status_code ==200 #This check that the connection to upload is good
def test_get_about(client):
    resp=client.get("/about")
    assert resp.status_code ==200 #This check that the connection to about is good
    assert b"Your Authors" in resp.data #This check if the cilent can grabs the data within about

def test_get_welcome(client):
    resp=client.get("/welcome")
    assert resp.status_code ==200 #This check that the connection to welcome is good
    assert b"Welcome" in resp.data  #This check if the cilent can grabs the data within welcome
def test_get_login(client):
    resp=client.get("/login")
    assert resp.status_code ==200 #This check that the connection to login is good
    assert b"Login Page" in resp.data  #This check if the cilent can grabs the data within login
    assert b"Login" in resp.data 
def test_get_sign_up_success(client):
    resp=client.get("/signup")
    assert resp.status_code ==200 #This check that the connection to signup is good
    assert b"Signup Page" in resp.data  #This check if the cilent can grabs the data within signup
    assert b"Sign Up" in resp.data

# user vincent username is username and password is password